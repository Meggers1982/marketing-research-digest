"""The three Claude calls, against a fake client. No API is touched."""
import json
from unittest import mock

import pytest

import digest_generator
import fact_checker
import llm
from conftest import FakeClient, FakeResponse

WORKS = [
    {"work_id": f"W{i}", "title": f"Paper {i}", "journal": "Journal of Marketing",
     "published": "2026-09-01", "doi": f"10.1/{i}", "abstract": "An abstract.",
     "source_id": "S1", "type": "article"}
    for i in range(1, 11)
]


def record(wid, **extra):
    base = {"work_id": wid, "headline": f"Headline {wid}", "the_study": "Five experiments.",
            "why_it_matters": "It matters.", "story_angle_primary": "Do this.",
            "story_angle_secondary": "Notice this.", "caveats": "Online panel."}
    base.update(extra)
    return base


def generate(answer, works=WORKS):
    client = FakeClient(answer)
    with mock.patch.object(digest_generator.anthropic, "Anthropic", return_value=client):
        md, records = digest_generator.generate_digest(
            works, focus_label="Pricing", subject_focus="pricing",
            primary_audience="marketers", secondary_audience="general readers",
            header="# Marketing Research Digest\n\n", api_key="test")
    return client, md, records


def test_text_of_skips_the_thinking_block():
    assert llm.text_of(FakeResponse("answer")) == "answer"


def test_bibliographic_fields_come_from_openalex_not_the_model():
    def answer(kwargs):
        # The model has no journal/DOI fields to fill; even junk in the prose
        # fields cannot reach the citation.
        return FakeResponse(json.dumps({"studies": [record("W1")]}))

    _, md, records = generate(answer)
    assert records[0]["journal"] == "Journal of Marketing"
    assert records[0]["doi"] == "10.1/1"
    assert records[0]["published"] == "2026-09-01"
    assert records[0]["paper_title"] == "Paper 1"
    assert "**Work ID:** W1 | **DOI:** 10.1/1" in md


def test_an_invented_or_repeated_work_id_is_dropped():
    def answer(kwargs):
        return FakeResponse(json.dumps({"studies": [record("W1"), record("W999"), record("W1")]}))

    _, _, records = generate(answer, works=WORKS[:1])
    assert [r["work_id"] for r in records] == ["W1"]


def test_input_is_batched_and_the_schema_is_sent():
    client, _, _ = generate(lambda kwargs: FakeResponse(json.dumps({"studies": []})))
    assert len(client.calls) == 2      # ten abstracts, eight per call
    fmt = client.calls[0]["output_config"]["format"]
    assert fmt["schema"] == digest_generator.STUDY_SCHEMA
    assert client.calls[0]["thinking"] == {"type": "adaptive"}


def test_a_truncated_batch_is_split_and_retried():
    def answer(kwargs):
        text = kwargs["messages"][0]["content"]
        n = text.count("--- W")
        if n > 4:
            return FakeResponse('{"studies": [', stop_reason="max_tokens")
        ids = [line.split()[1] for line in text.splitlines() if line.startswith("--- W")]
        return FakeResponse(json.dumps({"studies": [record(i) for i in ids]}))

    client, _, records = generate(answer, works=WORKS[:8])
    assert len(records) == 8
    assert len(client.calls) == 3      # one overrun, then two halves


def test_a_declined_batch_does_not_take_the_run_down():
    def answer(kwargs):
        response = FakeResponse("")
        response.stop_reason = "refusal"
        return response

    _, md, records = generate(answer)
    assert records == []
    assert "No studies were selected" in md


def test_no_articles_means_no_call():
    client, md, records = generate(lambda kwargs: pytest.fail("called"), works=[])
    assert records == [] and client.calls == []


def test_the_fact_check_keeps_one_verdict_per_study_it_was_sent():
    studies = [{"work_id": "W1"}, {"work_id": "W2"}]
    works = {w["work_id"]: w for w in WORKS[:2]}

    def answer(kwargs):
        verdict = lambda n, wid: {"number": n, "work_id": wid, "headline": "h",
                                  "verdict": "accurate", "notes": "", "issues": []}
        return FakeResponse(json.dumps({"studies": [
            verdict(2, "W2"), verdict(1, "W1"), verdict(3, "W404"), verdict(1, "W1")]}))

    client = FakeClient(answer)
    with mock.patch.object(fact_checker.anthropic, "Anthropic", return_value=client):
        md, records = fact_checker.run_fact_check(
            "digest", studies, works, title="T", run_date="2026-09-14",
            primary_audience="p", secondary_audience="s", api_key="k")
    assert [r["work_id"] for r in records] == ["W1", "W2"]
    assert "**Studies reviewed:** 2" in md
    assert "**Work ID:** W1 | **Verdict:** ✅ Accurate" in md


def test_the_fact_check_skips_the_call_when_nothing_was_selected():
    with mock.patch.object(fact_checker.anthropic, "Anthropic") as factory:
        md, records = fact_checker.run_fact_check(
            "digest", [], {}, title="T", run_date="2026-09-14",
            primary_audience="p", secondary_audience="s", api_key="k")
    factory.assert_not_called()
    assert records == []


def test_independent_calls_go_out_as_one_batch_not_live():
    client, _, _ = generate(lambda kwargs: FakeResponse(json.dumps({"studies": []})))
    assert len(client.batches_created) == 1
    assert len(client.batches_created[0]) == 2
    assert client.live_calls == []


def test_a_truncated_batch_goes_into_a_second_round():
    def answer(kwargs):
        text = kwargs["messages"][0]["content"]
        if text.count("--- W") > 4:
            return FakeResponse('{"studies": [', stop_reason="max_tokens")
        return FakeResponse(json.dumps({"studies": []}))

    client, _, _ = generate(answer, works=WORKS[:8])
    assert [len(b) for b in client.batches_created] == [1, 2]


def test_a_batch_past_the_deadline_is_canceled_and_run_live(monkeypatch):
    monkeypatch.setattr(llm, "BATCH_DEADLINE_SECONDS", 0)
    client = FakeClient(lambda kwargs: FakeResponse(json.dumps({"studies": []})),
                        batch_never_ends=True)
    with mock.patch.object(digest_generator.anthropic, "Anthropic", return_value=client):
        digest_generator.generate_digest(
            WORKS, focus_label="Pricing", subject_focus="pricing",
            primary_audience="marketers", secondary_audience="general readers",
            header="# H\n\n", api_key="test")
    assert client.canceled == ["msgbatch_0"]
    assert len(client.live_calls) == 2


def test_an_errored_batch_request_is_retried_live():
    client = FakeClient(lambda kwargs: FakeResponse(json.dumps({"studies": []})),
                        batch_result_type="errored")
    assert llm.complete_json(client, system="s", messages=[], schema={}, label="x") == {"studies": []}
    assert len(client.live_calls) == 1


def test_the_batch_api_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(llm, "USE_BATCH_API", False)
    client, _, _ = generate(lambda kwargs: FakeResponse(json.dumps({"studies": []})))
    assert client.batches_created == [] and len(client.live_calls) == 2
