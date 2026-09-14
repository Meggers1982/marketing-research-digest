"""Choose which articles the model sees.

OpenAlex hands back everything the journals published in the window --
editorials, errata, calls for papers, and (in the adjacent journals) a good
deal that is not marketing at all. The model is capped at MAX_ABSTRACTS a run,
so what fills those slots is decided here, cheaply and deterministically, and
every drop is counted so the dashboard can say what the run did not consider.

In order:

1. **Not research** -- OpenAlex types other than article/review, and titles that
   announce front matter ("Editorial", "Erratum", "Call for papers").
2. **No abstract** -- nothing to write up or fact-check against. Mostly Elsevier;
   see openalex.py.
3. **Off-topic in an adjacent journal** -- the 59 non-ABDC-marketing titles
   (AI & Society, Journal of Business Ethics, Appetite, Tobacco Control...)
   publish marketing research, but not only that. Their articles must mention
   a marketing term; the ABDC marketing journals are trusted to be on-beat.
4. **Already written up** -- any work ID or DOI a previous digest covered. The
   window is wider than a day and runs are daily, so without this the same
   article would be pitched again and again (new-scientist-story-ideas' PMID
   ledger, derived here from the archive instead of kept as a second file).
5. **Rank and cap** -- journal tier, recency and (on topic days) OpenAlex's
   relevance, with at most MAX_PER_JOURNAL from any one journal so one prolific
   title cannot fill the run.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import journals as journals_mod

KEEP_TYPES = {"article", "review"}

FRONT_MATTER = re.compile(
    r"^\s*(editorial|erratum|errata|corrigendum|correction|retraction|retracted|"
    r"call for papers|introduction to (the )?special issue|guest editorial|"
    r"reviewer acknowledg|book review|in memoriam|obituary|editor'?s note|"
    r"from the editor|commentary on|reply to|response to|expression of concern)",
    re.I,
)

MIN_ABSTRACT_CHARS = 400
MAX_ABSTRACT_CHARS = 3500

MARKETING_TERMS = re.compile(
    r"consumer|customer|marketing|market|brand|advertis|shopper|purchas|retail|"
    r"price|pricing|promotion|persuasi|sales|buyer|audience|influencer|"
    r"public relations|communication|reputation|tourist|visitor|donor|"
    r"e-commerce|platform|adoption|intention",
    re.I,
)


def is_research(work: dict) -> bool:
    return work.get("type") in KEEP_TYPES and not FRONT_MATTER.match(work.get("title") or "")


def is_adjacent(journal: journals_mod.Journal | None) -> bool:
    """Not on ABDC's marketing list: the list's own line between the peer group
    and the titles that merely publish some marketing research."""
    return journal is None or not journal.abdc


def covered_before(outputs_dir: Path) -> set[str]:
    """Every work ID and DOI a previous digest wrote up, lowercased."""
    seen = set()
    for path in outputs_dir.glob("*.json"):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for study in run.get("studies") or []:
            for key in (study.get("work_id"), study.get("doi")):
                if key and str(key).lower() not in {"not available", ""}:
                    seen.add(str(key).lower())
    return seen


def _recency_points(published: str, today: date) -> float:
    try:
        days = (today - date.fromisoformat(published[:10])).days
    except ValueError:
        return 0.0
    if days <= 14:
        return 2.0
    if days <= 30:
        return 1.5
    if days <= 60:
        return 1.0
    return 0.5


def priority(work: dict, journal: journals_mod.Journal | None, today: date,
             max_relevance: float) -> float:
    _, tier = journals_mod.tier_points(journal)
    relevance = 0.0
    if max_relevance and work.get("relevance"):
        relevance = 2.0 * float(work["relevance"]) / max_relevance
    return tier + _recency_points(work.get("published") or "", today) + relevance


def select(
    works: list[dict],
    outputs_dir: Path,
    max_abstracts: int = 40,
    max_per_journal: int = 3,
    today: date | None = None,
) -> tuple[list[dict], dict]:
    """(chosen works, counts of what was dropped and why)."""
    today = today or date.today()
    by_source = journals_mod.by_source_id()
    already = covered_before(outputs_dir)

    counts = {"found": len(works), "not_research": 0, "no_abstract": 0,
              "off_topic": 0, "already_covered": 0, "over_journal_cap": 0,
              "over_cap": 0, "sent": 0}
    eligible = []
    for work in works:
        if not is_research(work):
            counts["not_research"] += 1
            continue
        if len(work.get("abstract") or "") < MIN_ABSTRACT_CHARS:
            counts["no_abstract"] += 1
            continue
        journal = by_source.get(work.get("source_id", ""))
        if is_adjacent(journal) and not MARKETING_TERMS.search(
                f"{work.get('title', '')} {work.get('abstract', '')}"):
            counts["off_topic"] += 1
            continue
        keys = {str(work.get("work_id", "")).lower(), str(work.get("doi", "")).lower()} - {""}
        if keys & already:
            counts["already_covered"] += 1
            continue
        eligible.append((work, journal))

    max_relevance = max((float(w.get("relevance") or 0) for w, _ in eligible), default=0.0)
    eligible.sort(key=lambda pair: (
        -priority(pair[0], pair[1], today, max_relevance),
        pair[0].get("published") or "",
    ))

    chosen, per_journal = [], {}
    for work, _ in eligible:
        source = work.get("source_id") or work.get("journal")
        if per_journal.get(source, 0) >= max_per_journal:
            counts["over_journal_cap"] += 1
            continue
        if len(chosen) >= max_abstracts:
            counts["over_cap"] += 1
            continue
        per_journal[source] = per_journal.get(source, 0) + 1
        trimmed = dict(work)
        if len(trimmed["abstract"]) > MAX_ABSTRACT_CHARS:
            trimmed["abstract"] = trimmed["abstract"][:MAX_ABSTRACT_CHARS].rsplit(" ", 1)[0] + " …"
        chosen.append(trimmed)
    counts["sent"] = len(chosen)
    return chosen, counts
