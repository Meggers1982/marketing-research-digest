"""Fact-check the digest against the abstracts it was written from.

Forked from senior-research-digest. There, the fact-checker re-fetched each
abstract from PubMed; here the abstracts are the OpenAlex records the digest
was generated from, passed straight in -- a second fetch would return the same
text from the same source and only add a way to fail.
"""
from __future__ import annotations

import anthropic

import factcheck_render
import llm
import openalex

ANTHROPIC_TIMEOUT_SECONDS = 240.0
ANTHROPIC_MAX_RETRIES = 2


SYSTEM_PROMPT = """\
You are a rigorous research editor fact-checking a marketing and consumer-research
digest against the original published abstracts. For each study, compare the digest
text against the provided abstract and check four areas:

1. **Study facts** -- design (experiment, field experiment, survey, secondary data,
   interviews), number of studies, sample size (N), who the participants or data
   were (online panel, students, customers of a named firm, country), journal name
2. **Findings** -- numbers, percentages, effect sizes, direction of effect, which
   outcome was measured (stated intention vs. actual behavior), and whether a
   moderator or boundary condition the abstract names has been dropped
3. **Framing** -- no causal language for survey or observational findings; no
   generalizing a lab or online-panel result to "consumers" or "shoppers" at large;
   "Why it matters" doesn't leap beyond what the data support
4. **Story angles** -- no presenting a single study as a proven playbook; no hype
   language ("game-changer", "secret", "proven to boost sales", "revolutionize");
   angles appropriate for the stated primary/secondary audiences

## Spelling
Write your own commentary in American English ("analyze", "behavior", "randomized",
"center"). This does NOT apply to anything you quote: **As written:** and
**Abstract says:** must reproduce the digest and the abstract character for
character, British spellings included, and a spelling difference is never itself
an issue worth flagging. Journal titles and scale names also keep their original
spelling.

## What to return

Return one record per study in the digest, in the digest's own order:

- `number`: the study's number in the digest
- `work_id`: its work ID, copied exactly
- `headline`: its headline, copied from the digest
- `verdict`: one of "accurate", "minor", "significant"
- `notes`: a short note for the summary table, or "" when there is nothing to say
- `issues`: one record per problem found, empty when there are none. Each carries
  a short `label`, a `severity` of Minor / Moderate / Major, the `as_written`
  quote from the digest, what the `abstract_says`, the `problem` in plain
  language, and a `suggested_fix`.

## Severity
- **Minor** -- Small inaccuracy that doesn't change meaning (slightly wrong N, rounded stat)
- **Moderate** -- Overstates or misrepresents a finding (causal language for a survey,
  intention reported as behavior, a dropped boundary condition, a missing key limitation)
- **Major** -- Factually wrong, reverses the direction of a finding, or would lead a
  reader to act on incorrect information

## Scope
Check against the abstract only -- not the full text.
Claims that cannot be verified from the abstract: flag as "Unverifiable from abstract only."
If the digest already flags a limitation in Caveats, don't re-flag it unless the body
text contradicts the caveat.
An industry partner or funder named in the abstract that the digest omitted from
Caveats: flag as Moderate.

The report's headings, issue lettering and summary table are generated from these
records -- do not write them yourself.
"""

REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "studies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "integer"},
                    "work_id": {"type": "string"},
                    "headline": {"type": "string"},
                    "verdict": {"type": "string",
                                "enum": ["accurate", "minor", "significant"]},
                    "notes": {"type": "string"},
                    "issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                field: {"type": "string"}
                                for field in factcheck_render.ISSUE_FIELDS
                            },
                            "required": list(factcheck_render.ISSUE_FIELDS),
                            "additionalProperties": False,
                        },
                    },
                },
                "required": list(factcheck_render.STUDY_FIELDS),
                "additionalProperties": False,
            },
        }
    },
    "required": ["studies"],
    "additionalProperties": False,
}

STUDIES_PER_CALL = 10

SYSTEM_PROMPT_BLOCKS = [llm.cached(SYSTEM_PROMPT)]


def report_header(*, title: str, run_date: str, reviewed: int,
                  primary: str, secondary: str) -> str:
    return (
        f"# Fact-Check Report: {title}\n"
        f"**Checked:** {run_date} | **Studies reviewed:** {reviewed}\n"
        f"**Primary audience:** {primary} | **Secondary audience:** {secondary}\n\n"
        "---\n\n"
    )


def run_fact_check(
    digest_content: str,
    studies: list[dict],
    works: dict[str, dict],
    *,
    title: str,
    run_date: str,
    primary_audience: str,
    secondary_audience: str,
    api_key: str,
    model: str = llm.MODEL,
) -> tuple[str, list[dict]]:
    """Returns (report_markdown, verdict_records)."""

    def header(reviewed: int) -> str:
        return report_header(title=title, run_date=run_date, reviewed=reviewed,
                             primary=primary_audience, secondary=secondary_audience)

    # A run can legitimately select nothing; don't spend a call checking it.
    if not studies:
        print("  No studies selected; skipping fact check.")
        return header(0) + factcheck_render.render_report([]), []

    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=ANTHROPIC_TIMEOUT_SECONDS,
        max_retries=ANTHROPIC_MAX_RETRIES,
    )

    ids = [s["work_id"] for s in studies]
    batches = [ids[i:i + STUDIES_PER_CALL] for i in range(0, len(ids), STUDIES_PER_CALL)]

    # Every batch sends the same digest, so it goes first and carries the cache
    # breakpoint; only the batch-specific abstracts follow it. With the batch
    # number at the front (as before) the prefix differed on every call and each
    # batch paid a fresh 1.25x cache write that nothing ever read.
    shared = llm.cached(
        "Fact-check the digest below against the original abstracts. "
        "Check only the studies whose work IDs appear in the abstracts section.\n\n"
        f"**Primary audience:** {primary_audience}\n"
        f"**Secondary audience:** {secondary_audience}\n\n"
        f"{'=' * 60}\nDIGEST TO CHECK:\n\n{digest_content}\n\n"
    )

    records = []
    for index, batch in enumerate(batches, start=1):
        block = "\n\n".join(
            f"--- {wid} ---\n{openalex.format_for_model(works[wid])}"
            if wid in works else f"--- {wid} ---\nABSTRACT UNAVAILABLE"
            for wid in batch
        )
        batch_text = {
            "type": "text",
            "text": (
                f"Batch {index} of {len(batches)}.\n\n"
                f"{'=' * 60}\nORIGINAL ABSTRACTS:\n\n{block}\n{'=' * 60}"
            ),
        }
        try:
            parsed = llm.complete_json(
                client,
                system=SYSTEM_PROMPT_BLOCKS,
                messages=[{"role": "user", "content": [shared, batch_text]}],
                schema=REPORT_SCHEMA,
                label=f"fact-check batch {index}",
                model=model,
            )
        except llm.ModelDeclined as exc:
            print(f"  WARNING: fact-check batch {index} declined ({exc}); "
                  "its studies are reported as unchecked.")
            continue
        except ValueError as exc:
            # Truncated or unparseable. One batch, not the run.
            print(f"  WARNING: fact-check batch {index} returned unusable JSON "
                  f"({exc}); its studies are reported as unchecked.")
            continue
        records.extend(parsed.get("studies") or [])

    wanted = set(ids)
    seen, kept = set(), []
    for record in sorted(records, key=lambda r: r.get("number") or 0):
        wid = str(record.get("work_id", "")).strip()
        if wid in wanted and wid not in seen:
            seen.add(wid)
            kept.append(record)

    missing = [w for w in ids if w not in seen]
    if missing:
        print(f"  WARNING: {len(missing)} study/studies came back with no verdict.")

    return header(len(kept)) + factcheck_render.render_report(kept), kept
