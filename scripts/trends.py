"""Compare a new digest against the last one on the same topic, look for a
cross-study feature pitch, list a story idea per study, and keep a per-topic
memory file so all of that can draw on the topic's history rather than only the
most recent run.

Forked from senior-research-digest's trends.py. The previous digest is found
through the run records in outputs/*.json rather than by regex over every
markdown file, and the three visible sections are split out here so the
dashboard never has to parse them back.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import anthropic

import llm
from topics import normalize_topic

ANTHROPIC_TIMEOUT_SECONDS = 240.0
ANTHROPIC_MAX_RETRIES = 2

SECTIONS = {
    "trends": "Research Trends & Continuity",
    "feature_pitch": "Bigger Picture: Feature Pitch",
    "pitch_ideas": "Story Ideas by Study",
}

SYSTEM_PROMPT = """\
You are a research editor producing a short synthesis to run at the end of a
marketing research digest. The digest is read by a freelance journalist who pitches
stories to marketing and business trade press and to general-interest outlets.

You will be given the digest just written (NEW DIGEST), if one exists the most
recent digest on the same topic (PREVIOUS DIGEST), and a running cross-run summary
for this topic (TOPIC MEMORY, which may be empty if this is the first run). Write
exactly three visible sections plus one hidden block, using this structure and
headers verbatim:


## Spelling
Write in American English: "analyze", "behavior", "randomized", "center", "program".
Many of these journals are British and their abstracts are not written that way --
convert as you write in your own voice. Never change spelling inside something
reproduced verbatim: journal titles, scale and brand names, and direct quotations
keep their original form.

## Research Trends & Continuity

Compare the studies in the NEW digest against the studies in the PREVIOUS digest.
Identify genuine connections only -- do not force a link where none exists. Organize
under any of these that apply (omit any with nothing to report): **Convergent
findings**, **Advances**, **Counterpoints**, **New themes**. Name the specific study
headlines and work IDs from both digests for each point. If there is no previous
digest, write only: "_No prior digest on this topic to compare against yet -- this
is the first run._"

## Bigger Picture: Feature Pitch

Independent of the comparison above, look across ONLY the studies in the NEW digest
as a batch. Do several of them, taken together, point to a broader trend, an emerging
or underreported shift in how people buy or how brands behave, or a storyline that
would justify a standalone feature -- something bigger than any single study's own
story angles?

If yes, write:
**The pattern:** what the cross-study thread is, naming the specific study headlines
and work IDs from the NEW digest that support it (2-3 sentences).
**Why pitch this now:** why this is timely as a larger feature, not just as
individual items -- a platform change, a regulation, an economic pressure, a
cultural moment (1-2 sentences).
**Angle:** how a longer feature could be framed, and for which audience (1-2 sentences).
**Potential headlines:** 3 working headlines for the FEATURE itself, not for any
single study inside it -- each its own bullet. Vary them rather than writing one
headline three ways: one plain and concrete about what the evidence shows, one
that leads with the counterintuitive turn, one that names what is at stake for
the reader. Avoid the colon-plus-subtitle formula unless it genuinely earns its
place, avoid "Here's what X means for Y" constructions, and do not promise anything
the studies behind this pitch would not support.
**Potential outlets:** 3-4 real, currently active publications this specific pitch
could go to, each its own bullet with a short reason tied to THIS angle (not a
generic "they cover marketing"). Mix marketing and business trade press (for
example Marketing Week, Adweek, Ad Age, The Drum, Marketing Brew, Digiday, Retail
Dive, PRWeek, Harvard Business Review, MIT Sloan Management Review) with
general-interest outlets that run consumer-behavior and money stories where the
angle fits. Never name an outlet listed as already reporting these studies, and
never name one that wouldn't plausibly run this particular angle.

If the studies in this batch are disconnected single findings with no genuine
cross-study pattern, write only: "_No cross-study feature angle identified in this
batch._" Do not manufacture a pattern that isn't really there.

## Story Ideas by Study

Independent of both sections above, go through the studies in the NEW digest one
at a time -- not as a batch. For every study that has a genuinely pitchable angle
on its own, give it one line: a specific angle sharp enough for a writer to act
on, plus what kind of outlet or section it fits (for example: a marketing-trade
news brief, a CMO-audience column, a retail trade explainer, a personal-finance
column, a consumer-psychology explainer in a general-interest outlet).

Cover every study in the NEW digest worth pitching, not a curated handful. Skip
only a study that is genuinely thin or routine.

Name each study by its headline and work ID. Format as one bullet per study:

- **[Study headline] (Work ID [W number]):** [the angle], for [outlet type/section].

If nothing in the NEW digest has an individual pitch worth making, write only:
"_No individual study pitches identified in this digest._"

Finally, revise TOPIC MEMORY in light of the NEW digest and append it as a fenced
block (used internally -- do not explain it, and do not repeat its contents in any
visible section above):

```topic_memory
## Established findings
- [well-supported conclusions that have recurred across runs on this topic, with
  representative work IDs/dates]

## Emerging threads
- [newer patterns not yet established, worth watching in future runs]

## Feature ideas already pitched
- [short log of past "Bigger Picture" pitches, so future runs don't re-pitch the
  same angle]
```

Keep TOPIC MEMORY tight -- a dozen bullets total across all three subsections, not
a running log of every study. Merge, prune, or drop stale items rather than letting
the list grow. If TOPIC MEMORY was empty, base it only on the NEW digest.
"""

CONTINUATION_PROMPT = (
    "Continue exactly where you left off. Do not repeat any content already "
    "written, and do not restart from the beginning."
)


def slugify(topic: str) -> str:
    key = normalize_topic(topic)
    return re.sub(r"[^a-z0-9]+", "-", key).strip("-") or "broad"


def find_previous_digest(topic: str, outputs_dir: Path, before: str = "") -> str | None:
    """The markdown of the latest earlier run on the same topic, or None.

    Topic is compared through normalize_topic on both sides, so a rename cannot
    make the previous run invisible. `before` excludes the run being written.
    """
    key = normalize_topic(topic)
    best_date, best_md = "", None
    for path in outputs_dir.glob("*.json"):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if normalize_topic(run.get("topic", "")) != key:
            continue
        run_date = run.get("run_date", "")
        if before and run_date >= before:
            continue
        md_path = path.with_suffix(".md")
        if run_date > best_date and md_path.exists():
            best_date, best_md = run_date, md_path.read_text(encoding="utf-8")
    return best_md


def split_sections(body: str) -> dict[str, str]:
    """{"trends": ..., "feature_pitch": ..., "pitch_ideas": ...} from the prose."""
    out = {}
    for key, heading in SECTIONS.items():
        match = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=\n## |\Z)",
                          body, re.DOTALL | re.MULTILINE)
        out[key] = match.group(1).strip() if match else ""
    return out


def extract_memory(body: str) -> tuple[str, str | None]:
    """(visible body, memory block or None). A missing block -- a truncated
    response -- leaves the existing memory file untouched rather than replacing
    it with a partial one."""
    match = re.search(r"```topic_memory\s*(.*?)```", body, re.DOTALL)
    if not match:
        return body.strip(), None
    return body[: match.start()].rstrip(), match.group(1).strip()


def generate_trends_section(
    *,
    topic: str,
    topic_label: str,
    digest_content: str,
    outputs_dir: Path,
    memory_dir: Path,
    run_date: str,
    api_key: str,
    already_reporting: set[str] | None = None,
    model: str = llm.MODEL,
) -> str:
    """The three visible sections as markdown. Rewrites the topic memory file
    as a side effect."""
    previous = find_previous_digest(topic, outputs_dir, before=run_date)
    memory_path = memory_dir / f"{slugify(topic)}.md"
    existing_memory = (memory_path.read_text(encoding="utf-8") if memory_path.exists()
                       else "(none yet -- this is the first run on this topic)")
    reporting = ", ".join(sorted(already_reporting or [])) or "(none found or not checked)"

    user_message = (
        f"Topic: {topic_label}\n\n"
        f"OUTLETS ALREADY REPORTING THESE STUDIES: {reporting}\n\n"
        f"{'=' * 60}\nNEW DIGEST (just written):\n\n{digest_content}\n\n"
        f"{'=' * 60}\nPREVIOUS DIGEST:\n\n"
        f"{previous or '(none -- this is the first digest on this topic)'}\n\n"
        f"{'=' * 60}\nTOPIC MEMORY:\n\n{existing_memory}\n{'=' * 60}"
    )

    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=ANTHROPIC_TIMEOUT_SECONDS,
        max_retries=ANTHROPIC_MAX_RETRIES,
    )
    body = llm.complete_prose(
        client,
        # One call per run, so nothing is cache-marked: a write costs 1.25x input
        # and would only be read back if a continuation fired.
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        continuation_prompt=CONTINUATION_PROMPT,
        label="trends section",
        model=model,
    )

    visible, memory = extract_memory(body)
    if memory:
        memory_dir.mkdir(parents=True, exist_ok=True)
        updated = run_date or datetime.now().strftime("%Y-%m-%d")
        memory_path.write_text(
            f"# Topic Memory: {topic_label}\n_Last updated: {updated}_\n\n{memory}\n",
            encoding="utf-8",
        )
    return visible.strip()
