import pytest

import openalex


def test_abstracts_are_reassembled_in_position_order():
    inverted = {"consumers": [1], "Most": [0], "overpay.": [2]}
    assert openalex.reconstruct_abstract(inverted) == "Most consumers overpay."


def test_an_absent_abstract_is_empty_not_an_error():
    assert openalex.reconstruct_abstract(None) == ""
    assert openalex.reconstruct_abstract({}) == ""


def test_markup_and_the_leading_label_are_stripped():
    assert openalex.clean_abstract("<jats:p>Abstract: We find &amp; show</jats:p>") == "We find & show"
    # Only a leading label -- the word elsewhere is content.
    assert openalex.clean_abstract("Our abstract framing works") == "Our abstract framing works"


def test_ids_and_dois_are_bare():
    assert openalex.short_id("https://openalex.org/W4401234567") == "W4401234567"
    assert openalex.bare_doi("https://doi.org/10.1177/00222437") == "10.1177/00222437"
    assert openalex.bare_doi("") == ""


def test_a_work_is_normalized_to_the_fields_the_pipeline_uses():
    raw = {
        "id": "https://openalex.org/W1", "doi": "https://doi.org/10.1/x",
        "title": "<i>Price</i> fairness", "publication_date": "2026-09-01", "type": "article",
        "abstract_inverted_index": {"Hello": [0]},
        "primary_location": {"source": {"id": "https://openalex.org/S9", "display_name": "JMR"}},
        "relevance_score": 3.2,
    }
    work = openalex.normalize_work(raw)
    assert work == {
        "work_id": "W1", "doi": "10.1/x", "title": "Price fairness", "published": "2026-09-01",
        "type": "article", "journal": "JMR", "source_id": "S9", "abstract": "Hello",
        "relevance": 3.2,
    }


def test_search_pages_through_every_batch(monkeypatch):
    calls = []

    def fake_get(path, params):
        calls.append(params)
        ids = params["filter"].split(",")[0].split(":")[1].split("|")
        if params["cursor"] == "*":
            results = [{"id": f"https://openalex.org/W{ids[0]}", "title": "t"}]
            return {"results": results, "meta": {"next_cursor": "next"}}
        return {"results": [], "meta": {"next_cursor": None}}

    monkeypatch.setattr(openalex, "_get", fake_get)
    sources = [f"S{i}" for i in range(120)]
    works = openalex.search_works(sources, "2026-07-01", "2026-09-01", query="price")
    # 120 sources = three batches of 50, each paged until an empty page.
    assert len([c for c in calls if c["cursor"] == "*"]) == 3
    assert all("title_and_abstract.search:price" in c["filter"] for c in calls)
    assert {w["work_id"] for w in works} == {"WS0", "WS50", "WS100"}


def test_one_failed_batch_fails_the_run_rather_than_ship_a_partial_digest(monkeypatch):
    def fake_get(path, params):
        if "S0|" in params["filter"]:
            raise openalex.OpenAlexError("OpenAlex HTTP 503 on /works")
        return {"results": [{"id": "https://openalex.org/W7"}], "meta": {"next_cursor": None}}

    monkeypatch.setattr(openalex, "_get", fake_get)
    with pytest.raises(openalex.OpenAlexError, match="partial digest"):
        openalex.search_works([f"S{i}" for i in range(60)], "2026-07-01", "2026-09-01")


def test_every_batch_failing_is_loud(monkeypatch):
    def fake_get(path, params):
        raise openalex.OpenAlexError("down")

    monkeypatch.setattr(openalex, "_get", fake_get)
    with pytest.raises(openalex.OpenAlexError):
        openalex.search_works(["S1"], "2026-07-01", "2026-09-01")


def test_the_model_block_carries_the_work_id_not_a_pmid():
    block = openalex.format_for_model({
        "title": "T", "journal": "J", "published": "2026-09-01", "work_id": "W5",
        "doi": "", "abstract": "A",
    })
    assert "Work ID: W5" in block
    assert "DOI: Not available" in block
    assert "PMID" not in block
