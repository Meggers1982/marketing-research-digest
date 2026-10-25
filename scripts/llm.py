"""One place where this pipeline talks to Claude.

`digest_generator`, `fact_checker` and `trends` each grew their own copy of the
same call — model string, cache breakpoints, and a continuation loop for when a
response hits `max_tokens`. Two of the three copies drifted: `trends` never got
the retry and never got prompt caching, despite sending the largest payload of
the three (a whole new digest plus a whole previous one plus the topic memory).
(Caching was later taken back off `trends`: it makes one call per run, so a
cache write there is never read. Only prefixes reused across batch calls are
marked now.)

Reading the response is the part that has to be right. Under adaptive thinking
the first content block is a *thinking* block, so the old `response.content[0].text`
would have returned the wrong thing — or raised — the moment the model changed.
`text_of` walks the blocks instead.

Every call goes through the Message Batches API (`create_many`): half price on
input and output, in exchange for answers that arrive asynchronously, usually
within minutes. Nobody waits on a daily digest, so that trade is free here.
Independent calls (the digest and fact-check batches) go in as one batch; the
continuation loop sends one-request batches in turn because each turn needs
the previous answer.
"""
from __future__ import annotations

import os
import time

MODEL = "claude-opus-5"

# DIGEST_USE_BATCH_API=0 sends every call live at full price, for a manual run
# that has to finish now.
USE_BATCH_API = os.getenv("DIGEST_USE_BATCH_API", "1").lower() not in {"0", "false", "no", "off"}
BATCH_POLL_SECONDS = 30
# Most batches end within the hour, but the API allows 24. Past this deadline
# the batch is canceled and whatever did not finish runs live at full price, so
# a slow batch costs money rather than the day's digest.
BATCH_DEADLINE_SECONDS = 45 * 60
BATCH_CANCEL_WAIT_SECONDS = 5 * 60

# Non-streaming ceiling. The SDK wants streaming past this, and no call here
# needs a longer single turn than the continuation loop already provides.
MAX_TOKENS = 16000

MAX_CONTINUATIONS = 3


class ModelDeclined(RuntimeError):
    """The model returned `stop_reason: "refusal"`.

    Raised rather than returned so a caller can't mistake an empty string for
    ordinary output. Callers that have a deterministic fallback should catch it.
    """


class Truncated(ValueError):
    """A `complete_json` answer hit `max_tokens`, so the JSON is incomplete.

    A ValueError so callers that only catch that still survive it; its own type
    so a caller can tell "too much at once" (retry with less) from "did not
    parse" (retrying the same input will not help).
    """


def text_of(response) -> str:
    """Concatenate the response's text blocks.

    Adaptive thinking is on, so `content` opens with a thinking block whose
    `.text` is not the answer. Selecting by type is the only safe read.
    """
    return "".join(
        block.text
        for block in (response.content or [])
        if getattr(block, "type", None) == "text"
    )


def _params(*, system, messages, max_tokens, model, output_schema=None) -> dict:
    params = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
        "thinking": {"type": "adaptive"},
    }
    if output_schema is not None:
        params["output_config"] = {
            "format": {"type": "json_schema", "schema": output_schema}
        }
    return params


def _declined(response) -> ModelDeclined | None:
    if getattr(response, "stop_reason", None) != "refusal":
        return None
    details = getattr(response, "stop_details", None)
    return ModelDeclined(getattr(details, "category", None) or "unspecified")


def _wait_for_end(client, batch, deadline: float):
    while batch.processing_status != "ended" and time.monotonic() < deadline:
        time.sleep(BATCH_POLL_SECONDS)
        batch = client.messages.batches.retrieve(batch.id)
    return batch


def create_many(client, params_list: list[dict], *, label: str) -> list:
    """Run independent requests as one batch and return the Messages in order.

    A request that does not come back `succeeded` (errored, expired, or cut off
    by the deadline) is re-sent live, so the caller always gets one Message per
    request or the live call's exception.
    """
    if not params_list:
        return []
    if not USE_BATCH_API:
        return [client.messages.create(**p) for p in params_list]

    batch = client.messages.batches.create(requests=[
        {"custom_id": f"r{i}", "params": p} for i, p in enumerate(params_list)
    ])
    print(f"  {label}: batch {batch.id} submitted ({len(params_list)} request(s)).")
    batch = _wait_for_end(client, batch, time.monotonic() + BATCH_DEADLINE_SECONDS)
    if batch.processing_status != "ended":
        print(f"  WARNING: {label}: batch {batch.id} still running after "
              f"{BATCH_DEADLINE_SECONDS // 60} min; canceling it.")
        client.messages.batches.cancel(batch.id)
        batch = _wait_for_end(client, batch, time.monotonic() + BATCH_CANCEL_WAIT_SECONDS)

    out: list = [None] * len(params_list)
    if batch.processing_status == "ended":
        for result in client.messages.batches.results(batch.id):
            if result.result.type == "succeeded":
                out[int(result.custom_id[1:])] = result.result.message

    missing = [i for i, message in enumerate(out) if message is None]
    if missing:
        print(f"  WARNING: {label}: {len(missing)} of {len(params_list)} batch "
              "request(s) did not succeed; sending them live at full price.")
    for i in missing:
        out[i] = client.messages.create(**params_list[i])
    return out


def _create(client, *, system, messages, max_tokens, model, output_schema=None,
            label="call"):
    params = _params(system=system, messages=messages, max_tokens=max_tokens,
                     model=model, output_schema=output_schema)
    response = create_many(client, [params], label=label)[0]
    declined = _declined(response)
    if declined:
        raise declined
    return response


def complete_prose(
    client,
    *,
    system,
    messages,
    continuation_prompt: str,
    label: str,
    max_tokens: int = MAX_TOKENS,
    model: str = MODEL,
    max_continuations: int = MAX_CONTINUATIONS,
) -> str:
    """Run a prose call, continuing it if the response hits the token ceiling.

    `messages` is mutated with the turns that actually happened, which is what
    the model needs to see to pick up where it stopped. Only this turn's partial
    text is echoed back, not the accumulated body, so history doesn't duplicate.
    """
    response = _create(
        client, system=system, messages=messages,
        max_tokens=max_tokens, model=model, label=label,
    )
    chunk = text_of(response)
    body = chunk

    continuations = 0
    while response.stop_reason == "max_tokens" and continuations < max_continuations:
        messages.append({"role": "assistant", "content": chunk})
        messages.append({"role": "user", "content": continuation_prompt})
        response = _create(
            client, system=system, messages=messages,
            max_tokens=max_tokens, model=model,
            label=f"{label} continuation {continuations + 1}",
        )
        chunk = text_of(response)
        body += chunk
        continuations += 1

    if response.stop_reason == "max_tokens":
        print(
            f"  WARNING: {label} still truncated after {max_continuations} "
            "continuation(s) — output may be incomplete."
        )
    return body


def complete_json_many(
    client,
    calls: list[dict],
    *,
    label: str,
    max_tokens: int = MAX_TOKENS,
    model: str = MODEL,
) -> list:
    """Run independent schema-constrained calls in one batch.

    Each item of `calls` has `system`, `messages`, `schema` and `label`. Returns,
    in the same order, the parsed object or the exception for that call
    (ModelDeclined, Truncated, or a ValueError for unparseable JSON), so one bad
    call is the caller's to handle and the rest still count.

    There is deliberately no continuation loop here. A truncated JSON response
    cannot be repaired by concatenating the next turn's text the way prose can —
    the result is a broken document, not a shorter one. Callers keep responses
    inside one turn by batching their input instead.
    """
    import json

    responses = create_many(client, [
        _params(system=c["system"], messages=c["messages"], max_tokens=max_tokens,
                model=model, output_schema=c["schema"])
        for c in calls
    ], label=label)

    results: list = []
    for call, response in zip(calls, responses):
        declined = _declined(response)
        if declined:
            results.append(declined)
        elif response.stop_reason == "max_tokens":
            results.append(Truncated(
                f"{call['label']}: response hit max_tokens, so the JSON is incomplete. "
                "Send fewer items per call."
            ))
        else:
            try:
                results.append(json.loads(text_of(response)))
            except ValueError as exc:
                results.append(exc)
    return results


def complete_json(
    client,
    *,
    system,
    messages,
    schema: dict,
    label: str,
    max_tokens: int = MAX_TOKENS,
    model: str = MODEL,
):
    """One `complete_json_many` call; raises its exception instead of returning it."""
    [result] = complete_json_many(
        client, [{"system": system, "messages": messages, "schema": schema, "label": label}],
        label=label, max_tokens=max_tokens, model=model,
    )
    if isinstance(result, Exception):
        raise result
    return result


def cached(text: str) -> dict:
    """A text block marked as a prompt-cache breakpoint."""
    return {"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}
