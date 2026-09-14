"""The curated journal list, read from config/journals.csv.

The CSV is the source-verified list in ~/Documents/Marketing Research Journals
(208 titles: 149 ABDC field-of-research 3506 journals plus 59 adjacent,
practitioner and dead titles). It is copied here rather than referenced, so the
pipeline never depends on a file on one Mac. Edit it here; if the Documents
copy changes, re-copy it and re-run `resolve_sources.py`.

Two columns are added by `resolve_sources.py` and are not in the original:
`OpenAlex Source ID` and `OpenAlex Match`. The pipeline searches by source ID,
not ISSN: fourteen rows carry "unverified" or "n/a" in place of an ISSN, two
lost their leading zero or hyphen to a spreadsheet, and a source ID is the one
key that survives all of that.
"""
from __future__ import annotations

import csv
import functools
import re
from dataclasses import dataclass
from pathlib import Path

JOURNALS_CSV = Path(__file__).parent.parent / "config" / "journals.csv"

SOURCE_ID_COLUMN = "OpenAlex Source ID"
MATCH_COLUMN = "OpenAlex Match"

INACTIVE_CATEGORY = "Ceased / Dormant"
INACTIVE_STATUS = re.compile(r"^\s*(ceased|dormant)", re.I)


def normalize_issn(raw: str) -> str:
    """"0973-2586" from "09732586" or "9732594" -> "0973-2594"; "" for anything
    that is not an ISSN ("unverified", "n/a", "-").

    A spreadsheet reads an ISSN as a number, so the leading zero and the hyphen
    are the two things it drops. The check digit is not validated: a typo that
    passes the shape test simply fails to resolve and shows up in the match
    column."""
    text = (raw or "").strip().upper()
    if not text or text in {"-", "N/A"} or not re.search(r"\d", text):
        return ""
    compact = re.sub(r"[^0-9X]", "", text)
    if not re.fullmatch(r"\d{6,7}[\dX]", compact):
        return ""
    compact = compact.zfill(8)
    return f"{compact[:4]}-{compact[4:]}"


@dataclass(frozen=True)
class Journal:
    name: str
    category: str
    publisher: str
    issns: tuple[str, ...]
    abdc: str
    ajg: str
    ft50: bool
    status: str
    source_id: str
    match: str

    @property
    def active(self) -> bool:
        return self.category != INACTIVE_CATEGORY and not INACTIVE_STATUS.match(self.status)


@functools.lru_cache(maxsize=4)
def load(path: Path = JOURNALS_CSV) -> tuple[Journal, ...]:
    """Cached: scoring looks a journal up once per study."""
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    journals = []
    for row in rows:
        issns = tuple(dict.fromkeys(filter(None, (
            normalize_issn(row.get("ISSN (print)", "")),
            normalize_issn(row.get("ISSN (online)", "")),
        ))))
        journals.append(Journal(
            name=(row.get("Journal") or "").strip(),
            category=(row.get("Category") or "").strip(),
            publisher=(row.get("Publisher") or "").strip(),
            issns=issns,
            abdc=(row.get("ABDC 2025") or "").strip(),
            ajg=(row.get("AJG 2021") or "").strip(),
            ft50=(row.get("FT50") or "").strip().lower() == "yes",
            status=(row.get("Status") or "").strip(),
            source_id=(row.get(SOURCE_ID_COLUMN) or "").strip(),
            match=(row.get(MATCH_COLUMN) or "").strip(),
        ))
    return tuple(journals)


def active() -> list[Journal]:
    return [j for j in load() if j.active]


def searchable() -> list[Journal]:
    """Active journals OpenAlex actually indexes. The rest -- Think with Google,
    Nielsen Insights, Kantar BrandZ and the like -- publish, but not as a source
    OpenAlex carries, so a run cannot see them and says so."""
    return [j for j in active() if j.source_id]


# ------------------------------------------------------------------ journal tier

def tier_points(journal: Journal | None) -> tuple[str, int]:
    """(label, 0-5) from the list's own ratings.

    The ratings are the reason the list exists, so they are used directly
    instead of a hand-picked tier list. FT50 and ABDC A* are the elite peer
    group; an unrated title is a neutral 3, not a penalty -- it is mostly
    practitioner and adjacent journals (Tourism Management, Journal of Business
    Ethics) that ABDC files under another field, not weak ones.
    """
    if journal is None:
        return "unknown", 3
    if journal.ft50 or journal.abdc == "A*" or journal.ajg == "4*":
        return "A*", 5
    if journal.abdc == "A" or journal.ajg == "4":
        return "A", 4
    if journal.abdc == "B" or journal.ajg == "3":
        return "B", 3
    if journal.abdc == "C" or journal.ajg in {"2", "1"}:
        return "C", 2
    return "unrated", 3


def by_source_id() -> dict[str, Journal]:
    return {j.source_id: j for j in load() if j.source_id}


def find(name: str, source_id: str = "") -> Journal | None:
    """The journal a study ran in, by OpenAlex source ID first and name second.
    The model copies the journal name, so the name path has to tolerate case
    and a leading "The"."""
    journals = load()
    if source_id:
        for j in journals:
            if j.source_id == source_id:
                return j
    key = _name_key(name)
    for j in journals:
        if _name_key(j.name) == key:
            return j
    return None


def _name_key(name: str) -> str:
    text = re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower().replace("&", " and "))
    words = [w for w in text.split() if w not in {"the"}]
    return " ".join(words)
