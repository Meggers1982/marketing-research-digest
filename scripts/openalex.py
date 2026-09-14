"""Recent articles from the curated journals, via OpenAlex.

This replaces senior-research-digest's `pubmed.py`. PubMed indexes almost none
of these journals, so the source is OpenAlex (https://openalex.org): free, one
record per article with the journal it ran in, and an abstract for roughly
three in four articles. Measured 2026-09-14 over the 189 active titles: 1,089
works in the preceding 30 days from 138 journals, 760 of 1,012 research
articles with an abstract.

The gap is uneven, and it is a publisher gap, not a journal one: Elsevier does
not license abstracts to OpenAlex, so Journal of Business Research, Journal of
Retailing and Consumer Services and IJRM carry an abstract for about one
article in three. An article with no abstract cannot be written up or
fact-checked, so it is dropped before selection -- see `screening.py`, which
counts what it drops so the run can say so.

Anonymous use is capped at 1,000 list calls a day (the X-RateLimit headers say
so); a run makes about a dozen. Set OPENALEX_API_KEY to lift the cap.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.openalex.org"
USER_AGENT = "marketing-research-digest (https://github.com/Meggers1982/marketing-research-digest)"
TIMEOUT = 60
RETRIES = 3
RETRY_STATUS = {429, 500, 502, 503, 504}
PER_PAGE = 200
# OpenAlex allows up to 100 values in one OR filter; 50 keeps the URL short.
IDS_PER_CALL = 50
# A runaway query should not be able to spend the day's allowance.
MAX_PAGES_PER_BATCH = 10

WORK_FIELDS = (
    "id,doi,title,publication_date,type,abstract_inverted_index,"
    "primary_location,relevance_score"
)


class OpenAlexError(RuntimeError):
    pass


def _get(path: str, params: dict) -> dict:
    params = dict(params)
    key = os.environ.get("OPENALEX_API_KEY", "").strip()
    if key:
        params["api_key"] = key
    url = f"{BASE}{path}?{urllib.parse.urlencode(params, safe=':|,')}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in RETRY_STATUS and attempt < RETRIES:
                time.sleep(2 ** attempt)
                continue
            # The query is ours, the body is theirs: report the status only.
            raise OpenAlexError(f"OpenAlex HTTP {exc.code} on {path}") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < RETRIES:
                time.sleep(2 ** attempt)
                continue
            raise OpenAlexError(f"OpenAlex unreachable: {str(exc)[:100]}") from None
    raise OpenAlexError("OpenAlex: retries exhausted")


# ------------------------------------------------------------------ abstracts

def reconstruct_abstract(inverted: dict | None) -> str:
    """OpenAlex ships abstracts as {word: [positions]}; put the words back."""
    if not inverted:
        return ""
    slots: dict[int, str] = {}
    for word, positions in inverted.items():
        for position in positions or []:
            slots[position] = word
    text = " ".join(slots[i] for i in sorted(slots))
    return clean_abstract(text)


_LEADING_LABEL = re.compile(r"^\s*(abstract|summary)\s*[:.\-–—]?\s*", re.I)


def clean_abstract(text: str) -> str:
    """Strip the markup and the leading "Abstract" label some publishers deposit."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = " ".join(text.split())
    return _LEADING_LABEL.sub("", text, count=1).strip()


# ---------------------------------------------------------------------- works

def short_id(openalex_id: str) -> str:
    """"W4401234567" from "https://openalex.org/W4401234567"."""
    return (openalex_id or "").rstrip("/").rsplit("/", 1)[-1]


def bare_doi(doi: str) -> str:
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (doi or "").strip(), flags=re.I)


def normalize_work(raw: dict) -> dict:
    location = raw.get("primary_location") or {}
    source = location.get("source") or {}
    return {
        "work_id": short_id(raw.get("id", "")),
        "doi": bare_doi(raw.get("doi") or ""),
        "title": " ".join(html.unescape(re.sub(r"<[^>]+>", "", raw.get("title") or "")).split()),
        "published": raw.get("publication_date") or "",
        "type": raw.get("type") or "",
        "journal": source.get("display_name") or "",
        "source_id": short_id(source.get("id", "")),
        "abstract": reconstruct_abstract(raw.get("abstract_inverted_index")),
        "relevance": raw.get("relevance_score"),
    }


def search_works(
    source_ids: list[str],
    from_date: str,
    to_date: str,
    query: str = "",
) -> list[dict]:
    """Every work published in [from_date, to_date] in any of the sources,
    optionally narrowed by a boolean title-and-abstract query.

    Returns normalized works, de-duplicated by work ID. A batch that fails is
    reported and skipped rather than failing the run: one bad page should cost
    a slice of the journals, not the digest.
    """
    works: dict[str, dict] = {}
    calls = failed = 0
    for start in range(0, len(source_ids), IDS_PER_CALL):
        batch = source_ids[start:start + IDS_PER_CALL]
        filters = [
            "primary_location.source.id:" + "|".join(batch),
            f"from_publication_date:{from_date}",
            f"to_publication_date:{to_date}",
        ]
        if query:
            filters.append(f"title_and_abstract.search:{query}")
        cursor, pages = "*", 0
        while cursor and pages < MAX_PAGES_PER_BATCH:
            try:
                data = _get("/works", {
                    "filter": ",".join(filters),
                    "per-page": PER_PAGE,
                    "cursor": cursor,
                    "select": WORK_FIELDS,
                })
            except OpenAlexError as exc:
                print(f"  WARNING: {exc}; skipping {len(batch)} journal(s) in this batch.",
                      file=sys.stderr)
                failed += 1
                break
            calls += 1
            pages += 1
            results = data.get("results") or []
            for raw in results:
                work = normalize_work(raw)
                if work["work_id"]:
                    works.setdefault(work["work_id"], work)
            cursor = (data.get("meta") or {}).get("next_cursor")
            if not results:
                break
    print(f"  OpenAlex: {calls} call(s), {len(works)} work(s)"
          + (f", {failed} batch(es) failed" if failed else ""))
    if failed and not works:
        raise OpenAlexError("every OpenAlex batch failed")
    return list(works.values())


def format_for_model(work: dict) -> str:
    """The block the digest and fact-check prompts see for one article."""
    return "\n".join([
        f"Title: {work['title']}",
        f"Journal: {work['journal']}",
        f"Published: {work['published']}",
        f"Work ID: {work['work_id']}",
        f"DOI: {work['doi'] or 'Not available'}",
        "",
        f"Abstract: {work['abstract']}",
    ])


# ------------------------------------------------------------------- sources

def sources_by_issn(issns: list[str]) -> dict[str, dict]:
    """{issn: source} for every ISSN OpenAlex knows, batched."""
    found: dict[str, dict] = {}
    for start in range(0, len(issns), IDS_PER_CALL):
        batch = issns[start:start + IDS_PER_CALL]
        data = _get("/sources", {
            "filter": "issn:" + "|".join(batch),
            "per-page": PER_PAGE,
            "select": "id,display_name,issn,issn_l,works_count,type",
        })
        for source in data.get("results") or []:
            for issn in source.get("issn") or []:
                found.setdefault(issn, source)
    return found


def sources_by_name(name: str) -> list[dict]:
    data = _get("/sources", {
        "search": name,
        "per-page": 5,
        "select": "id,display_name,issn,works_count,type",
    })
    return data.get("results") or []
