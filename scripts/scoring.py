"""How pitchable is a study?

Deliberately deterministic, as in senior-research-digest: every input is
something the pipeline already holds -- the journal's rating, when it
published, what design the write-up describes, how large the sample was,
whether the press has had it, and what the fact-checker said. Nothing is asked
of a model, because a score a model assigns cannot be reproduced on a re-run
and cannot be unit-tested.

What changed from the fork:

- **Design** is marketing's evidence ladder, not medicine's. A field experiment
  or a large behavioral dataset (real purchases, real platform data) is the
  strongest pitch; a multi-study lab or online-panel experiment next; a survey
  analyzed with a structural model is common in these journals and scores low
  because it measures stated attitudes, not behavior.
- **Journal tier** comes from the list's own ratings (FT50, ABDC, AJG) via
  `journals.tier_points`, not a hand-picked list.

Bands, not ranks: two studies a few points apart are not meaningfully
different. The thresholds are senior-research-digest's (tuned there so each band
held a distinct slice of 1,122 studies) and have not been re-tuned against this
archive yet -- that wants two weeks of runs first.
"""
from __future__ import annotations

import re

import journals as journals_mod

WEIGHTS = {
    "evidence_type": 3,
    "coverage_gap": 3,
    "journal_tier": 2,
    "recency": 2,
    "sample_size": 1,
    "accuracy": 1,
}

SCORE_BANDS = ((82, "Lead"), (72, "Strong"), (62, "Worth a look"), (0, "Background"))
BAND_ORDER = [name for _, name in SCORE_BANDS]
# "Lead" claims the story is open, which is exactly what an unchecked study has
# no evidence for.
UNCHECKED_COVERAGE_CEILING = "Strong"


def score_band(score) -> str:
    for floor, name in SCORE_BANDS:
        if score >= floor:
            return name
    return "Background"


def cap_band(band: str, ceiling: str) -> str:
    """Return whichever of the two is weaker."""
    try:
        return band if BAND_ORDER.index(band) >= BAND_ORDER.index(ceiling) else ceiling
    except ValueError:
        return band


def story_score(components: dict) -> int:
    """Weighted 0-5 components rescaled to 0-100. A component that is None was
    not measured and is dropped from both halves of the fraction rather than
    scored as a middling value."""
    known = {k: v for k, v in components.items() if v is not None and k in WEIGHTS}
    if not known:
        return 0
    total = sum(WEIGHTS[k] * min(5, max(0, v)) for k, v in known.items())
    return round(100 * total / (5 * sum(WEIGHTS[k] for k in known)))


# ---------------------------------------------------------------- evidence type

# Ordered: the first pattern that matches wins, so the strongest design a
# write-up claims is the one recorded.
EVIDENCE_PATTERNS = (
    ("meta-analysis", 5, r"meta-analy|pooled (?:analysis|data) (?:of|from)"),
    ("field experiment", 5,
     r"field experiment|natural experiment|quasi-experiment|a/b test|"
     r"randomi[sz]ed (?:controlled|field)|difference-in-differences"),
    ("behavioral data", 4,
     r"transaction|scanner data|panel data|clickstream|purchase (?:data|records|histor)|"
     r"sales data|platform data|archival|secondary data|field data|"
     r"(?:million|billion) (?:consumers|customers|transactions|reviews|posts|users|observations)|"
     r"[\d,]{5,} (?:transactions|reviews|posts|tweets|observations|purchases)"),
    ("experiments", 4,
     r"experiment|randomly assigned|between-subjects|within-subjects|"
     r"(?:two|three|four|five|six|seven|eight|\d) (?:online |lab |laboratory )?studies|"
     r"preregistered"),
    ("modeling", 3,
     r"econometric|simulation|analytical model|game-theoretic|machine learning|"
     r"text analysis|natural language processing"),
    ("survey", 2,
     r"survey|questionnaire|structural equation|\bpls-sem\b|\bsem\b|respondents"),
    ("qualitative", 2,
     r"interview|ethnograph|qualitative|focus group|netnograph|case study|grounded theory"),
    ("review", 1, r"systematic review|literature review|bibliometric|review of (?:the )?research"),
    ("conceptual", 1, r"conceptual (?:paper|framework|model)|theoretical framework|we propose a framework"),
)


def evidence_type(text: str) -> tuple[str, int]:
    """(label, 0-5). "unspecified" scores 2 -- a write-up that omits the design
    is not evidence of a weak one."""
    blob = (text or "").lower()
    for label, points, pattern in EVIDENCE_PATTERNS:
        if re.search(pattern, blob):
            return label, points
    return "unspecified", 2


# ------------------------------------------------------------------ sample size

_UNITS = (r"participants|respondents|consumers|customers|shoppers|users|adults|people|"
          r"students|employees|managers|firms|companies|brands|households|visitors|"
          r"tourists|donors|patients|parents|women|men")
_N_PATTERNS = (
    r"\b[nN]\s*=\s*([\d,]{2,})",
    rf"\b([\d,]{{3,}})\s+(?:[a-z-]+\s+)?(?:{_UNITS})\b",
    r"\bdata from\s+([\d,]{3,})\b",
    r"\b(\d+(?:\.\d+)?)\s+million\s+(?:" + _UNITS + r")\b",
)


def sample_size(text: str) -> tuple[int | None, int]:
    """(largest N found, 0-5). Unknown scores 2, the same neutral as an
    unstated design."""
    blob = text or ""
    best = None
    for index, pattern in enumerate(_N_PATTERNS):
        for raw in re.findall(pattern, blob, flags=re.I):
            try:
                value = float(raw.replace(",", ""))
            except ValueError:
                continue
            if index == 3:
                value *= 1_000_000
            value = int(value)
            if value > (best or 0):
                best = value
    if best is None:
        return None, 2
    for floor, points in ((10000, 5), (1000, 4), (300, 3), (100, 2), (0, 1)):
        if best >= floor:
            return best, points
    return best, 1


# --------------------------------------------------------------------- recency

def _year_month(value: str) -> tuple[int, int] | None:
    match = re.search(r"(\d{4})-(\d{2})", value or "")
    return (int(match.group(1)), int(match.group(2))) if match else None


def recency(published: str, run_date: str) -> int:
    """0-5 by months between publication and the run. Undated scores 0: a date
    the pipeline could not read is a real gap. OpenAlex dates are ISO, so there
    is none of the month-name parsing that fabricated June in the fork."""
    published_at, run_at = _year_month(published), _year_month(run_date)
    if not published_at or not run_at:
        return 0
    months = (run_at[0] - published_at[0]) * 12 + (run_at[1] - published_at[1])
    if months < 0:          # an issue date ahead of the online-first date
        return 5
    for limit, points in ((1, 5), (3, 4), (6, 3), (12, 2), (24, 1)):
        if months <= limit:
            return points
    return 0


# --------------------------------------------------------------- coverage & QA

COVERAGE_POINTS = {"unreported": 5, "lightly_reported": 2, "widely_reported": 0}


def coverage_gap(state: str | None) -> int | None:
    """0-5, or None when nobody looked. Absence of coverage is usually evidence
    that nobody looked, so an unchecked study drops the component."""
    if not state:
        return None
    return COVERAGE_POINTS.get(state)


VERDICT_POINTS = {"accurate": 5, "minor": 2, "significant": 0}


def accuracy(verdict: str | None) -> int | None:
    """0-5 from the fact-checker's verdict ("accurate" / "minor" /
    "significant"), or None if it never ran."""
    if not verdict:
        return None
    return VERDICT_POINTS.get(str(verdict).strip().lower(), 3)


# ------------------------------------------------------------------- the scorer

def score_study(study: dict, run_date: str = "", coverage_state=None, verdict=None) -> dict:
    """The score, its band and every component that produced them -- a bare
    number is not reviewable."""
    body = " ".join(filter(None, [
        study.get("the_study", ""), study.get("why_it_matters", ""),
        study.get("caveats", ""), study.get("paper_title", ""),
    ]))
    design, design_points = evidence_type(body)
    participants, size_points = sample_size(body)
    journal = journals_mod.find(study.get("journal", ""), study.get("source_id", ""))
    tier, tier_points = journals_mod.tier_points(journal)

    components = {
        "evidence_type": design_points,
        "coverage_gap": coverage_gap(coverage_state),
        "journal_tier": tier_points,
        "recency": recency(study.get("published", ""), run_date),
        "sample_size": size_points,
        "accuracy": accuracy(verdict),
    }
    score = story_score(components)
    band = score_band(score)
    if components["coverage_gap"] is None:
        band = cap_band(band, UNCHECKED_COVERAGE_CEILING)
    return {
        "score": score,
        "band": band,
        "evidence_type": design,
        "sample_size": participants,
        "journal_tier": tier,
        "coverage_state": coverage_state or "",
        "components": components,
    }
