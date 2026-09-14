"""Turn study records into the digest's markdown.

The model returns records (see digest_generator.STUDY_SCHEMA) and this module
renders them, so the markdown is a fixed template rather than prose the model
chose the shape of. senior-research-digest learned why the hard way: its
dashboard regex-scraped model-written markdown, the model changed one heading
level, and half the archive silently lost its fact-check verdicts.

This repo goes one step further. The dashboard is built from the records
themselves (the run's .json file in outputs/), so this markdown is for people
-- the archive you can read on GitHub -- and nothing parses it back.
"""
from __future__ import annotations

STUDY_FIELDS = (
    "headline", "journal", "published", "work_id", "doi",
    "the_study", "why_it_matters",
    "story_angle_primary", "story_angle_secondary", "caveats",
)


def _clean(value) -> str:
    """One line, no stray pipes -- a pipe would break the citation table row."""
    return " ".join(str(value or "").split()).replace("|", "/")


def doi_or_placeholder(value) -> str:
    return _clean(value) or "Not available"


def render_study(number: int, study: dict, primary: str, secondary: str) -> str:
    return "\n".join([
        f"### {number}. {_clean(study.get('headline'))}",
        "",
        f"**Journal:** *{_clean(study.get('journal'))}* | "
        f"**Published:** {_clean(study.get('published'))}",
        f"**Work ID:** {_clean(study.get('work_id'))} | **DOI:** {doi_or_placeholder(study.get('doi'))}",
        "",
        f"**The study:** {_clean(study.get('the_study'))}",
        "",
        f"**Why it matters:** {_clean(study.get('why_it_matters'))}",
        "",
        "**Story angles:**",
        f"- **For {primary}:** {_clean(study.get('story_angle_primary'))}",
        f"- **For {secondary}:** {_clean(study.get('story_angle_secondary'))}",
        "",
        f"**Caveats:** {_clean(study.get('caveats')) or 'None significant'}",
        "",
        "---",
        "",
    ])


def render_citation_table(studies: list[dict]) -> str:
    rows = "\n".join(
        f"| {i} | {_clean(s.get('work_id'))} | {_clean(s.get('journal'))} | "
        f"{_clean(s.get('published'))} | {doi_or_placeholder(s.get('doi'))} |"
        for i, s in enumerate(studies, start=1)
    )
    return "\n".join([
        "## Citation Reference",
        "",
        "| # | Work ID | Journal | Date | DOI |",
        "|---|---------|---------|------|-----|",
        rows,
        "",
    ])


def render_digest(studies: list[dict], primary: str, secondary: str) -> str:
    """The body of the digest: every entry, then the citation table."""
    if not studies:
        return "_No studies were selected for this run._\n"
    entries = "".join(
        render_study(i, s, primary, secondary)
        for i, s in enumerate(studies, start=1)
    )
    return entries + render_citation_table(studies)
