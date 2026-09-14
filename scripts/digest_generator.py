"""Write the digest: the model selects the newsworthy articles and returns one
record per study; `digest_render` turns the records into markdown.

Forked from senior-research-digest's generator. Two changes beyond the prompt:

- **Bibliographic fields are not the model's to write.** Journal, date and DOI
  come from OpenAlex and are stamped onto each record after the call. The
  model only echoes the work ID, and a record citing a work ID that was not
  sent is dropped -- an invented citation is worse than a study left out.
- The abstract block carries the OpenAlex work ID instead of a PMID.
"""
from __future__ import annotations

from datetime import datetime

import anthropic

import digest_render
import llm
import openalex

# Bounded below the workflow step's timeout so a stalled call fails, retries and
# reports instead of taking the whole run down (senior-research-digest MEA-244).
ANTHROPIC_TIMEOUT_SECONDS = 240.0
ANTHROPIC_MAX_RETRIES = 2

DIGEST_TITLE = "Marketing Research Digest"

SYSTEM_PROMPT = """\
You are an expert business and science journalist producing a curated research
digest on marketing, advertising, branding and consumer behavior. You will be given
abstracts from peer-reviewed marketing, advertising, consumer research and adjacent
journals, found through OpenAlex.

Select the most newsworthy studies and write a structured entry for each one.

## Selection criteria
- Prioritize: empirical evidence about real people or real markets -- field
  experiments, large behavioral datasets (transactions, platform or scanner data),
  multi-study experimental papers, meta-analyses
- Favor findings with a clear, surprising or usable takeaway: something a marketer
  could act on, or something that reveals how people actually shop, spend, decide,
  or respond to brands and persuasion
- Skip: editorials, purely conceptual or theoretical papers with no new evidence,
  bibliometric and literature reviews, methodology-only papers, and survey studies
  whose only result is a set of significant paths in a structural model -- unless
  the finding itself is genuinely striking

## Spelling
Write in American English: "analyze", "behavior", "randomized", "center", "program",
"generalize". Many of these journals are British and their abstracts are not written
that way -- convert as you write in your own voice. Never change spelling inside
something reproduced verbatim: journal titles (e.g. *Journal of Consumer Behaviour*),
scale, instrument and brand names, and direct quotations keep their original form.

## What to return

Return one record per selected study. Field by field:

- `work_id`: exactly as given in the abstract block (it starts with "W"). Never
  invent or alter one.
- `headline`: compelling, plain-language, not the paper's own title
- `the_study`: what the researchers did and with whom -- the design (for example
  "five online experiments", "a field experiment with a European grocery chain",
  "an analysis of 1.2 million transactions"), the sample and its size (N=, who
  they were, which country, whether an online panel such as MTurk or Prolific, or
  students), and the key finding in plain language. 2-4 sentences.
- `why_it_matters`: the practical significance. 1-2 sentences.
- `story_angle_primary`: an angle for [PRIMARY_AUDIENCE] -- what to test, change,
  question or watch for. Lab and online-panel experiments show what can happen,
  not what will happen at scale; frame the angle that way rather than as a proven
  playbook.
- `story_angle_secondary`: an angle for [SECONDARY_AUDIENCE] -- what the finding
  reveals about everyday life: how people shop, spend, choose, or get persuaded.
  A different framing, not the first angle addressed to a different reader. Where
  a study supports no real angle for them, say so briefly rather than padding.
- `caveats`: flag any that apply -- online panel or student sample; hypothetical
  scenarios or vignettes rather than real purchases; stated intentions rather than
  observed behavior; cross-sectional survey (cannot establish causation); a single
  country, firm, platform or category; small N (under 100 per condition for an
  experiment, under 200 for a survey); short time horizon; an industry partner or
  funder (name it). "None significant" if none do.

Select only the studies worth writing up. Returning fewer records than there are
abstracts is expected and correct; a weak study left out is better than a weak
entry written up.
"""

MODEL_FIELDS = (
    "work_id", "headline", "the_study", "why_it_matters",
    "story_angle_primary", "story_angle_secondary", "caveats",
)

# One record per study, so a malformed answer is an API-level error rather than a
# regex that quietly matches nothing.
STUDY_SCHEMA = {
    "type": "object",
    "properties": {
        "studies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {field: {"type": "string"} for field in MODEL_FIELDS},
                "required": list(MODEL_FIELDS),
                "additionalProperties": False,
            },
        }
    },
    "required": ["studies"],
    "additionalProperties": False,
}

# A JSON answer cannot be stitched back together across turns the way prose can,
# so the input is batched to keep every answer inside one turn. Eight is where
# senior-research-digest settled after Opus 5's longer records overran ten
# (MEA-373 there). A batch that still overruns is split in half and retried, so
# a wrong size costs extra calls, not studies.
ABSTRACTS_PER_CALL = 8


def digest_header(*, run_date: str, days_back: int, journal_count: int,
                  screened: int, found: int, focus_label: str,
                  primary: str, secondary: str) -> str:
    return "\n".join([
        f"# {DIGEST_TITLE}",
        f"**Run date:** {run_date} | **Coverage window:** Last {days_back} days",
        f"**Journals searched:** {journal_count} | **Articles screened:** "
        f"{screened} (of {found} published)",
        f"**Focus:** {focus_label}",
        f"**Primary audience:** {primary} | **Secondary audience:** {secondary}",
    ]) + "\n\n---\n\n"


def stamp(record: dict, work: dict) -> dict:
    """The model's prose plus OpenAlex's bibliographic facts."""
    return {
        **{field: " ".join(str(record.get(field) or "").split()) for field in MODEL_FIELDS},
        "work_id": work["work_id"],
        "journal": work["journal"],
        "published": work["published"],
        "doi": work["doi"],
        "paper_title": work["title"],
        "source_id": work.get("source_id", ""),
    }


def generate_digest(
    works: list[dict],
    *,
    focus_label: str,
    subject_focus: str,
    primary_audience: str,
    secondary_audience: str,
    header: str,
    api_key: str,
    model: str = llm.MODEL,
) -> tuple[str, list[dict]]:
    """Returns (digest_markdown, study_records), records in digest order."""
    if not works:
        return header + "_No articles with usable abstracts were found for this run._\n", []

    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=ANTHROPIC_TIMEOUT_SECONDS,
        max_retries=ANTHROPIC_MAX_RETRIES,
    )
    system = [llm.cached(
        SYSTEM_PROMPT
        .replace("[PRIMARY_AUDIENCE]", primary_audience)
        .replace("[SECONDARY_AUDIENCE]", secondary_audience)
    )]
    focus_line = f"**Subject focus:** {subject_focus}\n" if subject_focus else ""

    by_id = {w["work_id"]: w for w in works}
    ids = list(by_id)
    pending = [ids[i:i + ABSTRACTS_PER_CALL] for i in range(0, len(ids), ABSTRACTS_PER_CALL)]
    total = len(pending)
    index = 0
    records: list[dict] = []
    while pending:
        batch = pending.pop(0)
        index += 1
        block = "\n\n".join(
            f"--- {wid} ---\n{openalex.format_for_model(by_id[wid])}" for wid in batch
        )
        message = (
            f"Batch {index} of {total}. Write up the newsworthy studies among "
            f"the {len(batch)} abstracts below.\n\n"
            f"**Primary audience:** {primary_audience}\n"
            f"**Secondary audience:** {secondary_audience}\n"
            + focus_line
            + f"\n{'=' * 60}\n{block}\n{'=' * 60}"
        )
        try:
            parsed = llm.complete_json(
                client,
                system=system,
                messages=[{"role": "user", "content": message}],
                schema=STUDY_SCHEMA,
                label=f"digest batch {index}",
                model=model,
            )
        except llm.ModelDeclined as exc:
            print(f"  WARNING: batch {index} declined ({exc}); its studies are omitted.")
            continue
        except llm.Truncated:
            if len(batch) > 1:
                half = len(batch) // 2
                pending[:0] = [batch[:half], batch[half:]]
                total += 1
                print(f"  WARNING: batch {index} hit max_tokens with {len(batch)} "
                      "abstracts; retrying it as two halves.")
            else:
                print(f"  WARNING: batch {index} hit max_tokens on one abstract; omitted.")
            continue
        except ValueError as exc:
            print(f"  WARNING: batch {index} returned unusable JSON ({exc}); "
                  "its studies are omitted.")
            continue
        records.extend(parsed.get("studies") or [])

    kept, seen, dropped = [], set(), 0
    for record in records:
        wid = str(record.get("work_id", "")).strip()
        if wid not in by_id or wid in seen:
            dropped += 1
            continue
        seen.add(wid)
        kept.append(stamp(record, by_id[wid]))
    if dropped:
        print(f"  WARNING: dropped {dropped} record(s) citing a work ID that was not "
              "in this run (or citing one twice).")

    body = digest_render.render_digest(kept, primary_audience, secondary_audience)
    return header + body, kept


def run_date_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")
