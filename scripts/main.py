"""Daily marketing research digest -- entry point for GitHub Actions.

OpenAlex (recent articles from the curated journals) -> screening (what the
model gets to see) -> Claude (digest records) -> Claude (fact check) -> Google
News (has the press already had it?) -> Claude (trends, feature pitch, story
ideas) -> outputs/ -> dashboard data.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import journals as journals_mod
import openalex
import screening
import topics
import web_coverage
from build_dashboard_data import main as rebuild_dashboard_data
from digest_generator import DIGEST_TITLE, digest_header, generate_digest
from fact_checker import run_fact_check
from trends import generate_trends_section, split_sections
import llm

REPO_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
TOPIC_MEMORY_DIR = REPO_ROOT / "topic_memory"
CONFIG_PATH = REPO_ROOT / "config" / "digest_config.json"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def pick_subject_focus(config: dict, now: datetime) -> str:
    """Today's topic. Priority: the DIGEST_FOCUS env var (workflow_dispatch
    input), then a fixed config["subject_focus"], then the rotation by day of
    year. "" means a broad run."""
    override = os.environ.get("DIGEST_FOCUS", "").strip()
    if override:
        return override
    fixed = (config.get("subject_focus") or "").strip()
    if fixed:
        return fixed
    rotation = config.get("focus_rotation")
    if rotation is None:
        rotation = topics.DEFAULT_ROTATION
    if not rotation:
        return ""
    day = now.timetuple().tm_yday
    focus = rotation[day % len(rotation)]
    print(f"Rotating focus #{day % len(rotation)}: '{focus or '(broad)'}'")
    return focus


def digest_stem(focus_label: str, run_date: str) -> str:
    return f"{DIGEST_TITLE} — {focus_label} — {run_date}"


def unique_stem(stem: str) -> str:
    """A second run on the same day becomes "(Part 2)" rather than overwriting."""
    if not (OUTPUTS_DIR / f"{stem}.json").exists() and not (OUTPUTS_DIR / f"{stem}.md").exists():
        return stem
    n = 2
    while (OUTPUTS_DIR / f"{stem} (Part {n}).json").exists():
        n += 1
    return f"{stem} (Part {n})"


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY is not set.")

    config = load_config()
    now = datetime.now(timezone.utc)
    run_date = now.strftime("%Y-%m-%d")
    days_back = int(config.get("days_back", 60))
    window_from = (now - timedelta(days=days_back)).strftime("%Y-%m-%d")
    primary = config["primary_audience"]
    secondary = config["secondary_audience"]

    subject_focus = pick_subject_focus(config, now)
    topic = topics.normalize_topic(subject_focus)
    focus_label = topics.label_for(subject_focus)
    query = topics.query_for(subject_focus)

    searchable = journals_mod.searchable()
    not_indexed = [j.name for j in journals_mod.active() if not j.source_id]
    OUTPUTS_DIR.mkdir(exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"Marketing Research Digest — {now:%Y-%m-%d %H:%M} UTC")
    print(f"Journals  : {len(searchable)} searchable ({len(not_indexed)} active titles not in OpenAlex)")
    print(f"Window    : {window_from} to {run_date}")
    print(f"Focus     : {focus_label}")
    print(f"{'=' * 60}\n")

    # ── Step 1: OpenAlex ────────────────────────────────────────────────────
    print("Searching OpenAlex across the curated journals...")
    works = openalex.search_works([j.source_id for j in searchable], window_from, run_date, query)
    if not works:
        print("No articles found. Exiting.")
        sys.exit(0)

    # ── Step 2: Screening ───────────────────────────────────────────────────
    chosen, counts = screening.select(
        works, OUTPUTS_DIR,
        max_abstracts=int(config.get("max_abstracts", 40)),
        max_per_journal=int(config.get("max_per_journal", 3)),
        today=now.date(),
    )
    print("Screening: " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in counts.items()))
    if not chosen:
        print("Nothing left to write up after screening. Exiting.")
        sys.exit(0)
    by_id = {w["work_id"]: w for w in chosen}

    stem = unique_stem(digest_stem(focus_label, run_date))
    header = digest_header(
        run_date=run_date, days_back=days_back, journal_count=len(searchable),
        screened=len(chosen), found=counts["found"], focus_label=focus_label,
        primary=primary, secondary=secondary,
    )

    # ── Step 3: Digest ──────────────────────────────────────────────────────
    print("\nGenerating digest...")
    digest_md, studies = generate_digest(
        chosen, focus_label=focus_label, subject_focus=subject_focus,
        primary_audience=primary, secondary_audience=secondary,
        header=header, api_key=api_key,
    )
    print(f"Digest generated — {len(studies)} studies selected")

    # ── Step 4: Fact check ──────────────────────────────────────────────────
    print("\nRunning fact checker...")
    fact_md, verdicts = run_fact_check(
        digest_md, studies, by_id,
        title=stem, run_date=run_date,
        primary_audience=primary, secondary_audience=secondary, api_key=api_key,
    )

    # ── Step 5: Has the press already had it? ───────────────────────────────
    print("\nChecking web coverage...")
    coverage = web_coverage.check_digest(
        [(s["work_id"], s["headline"]) for s in studies], days_back=days_back,
    )
    if coverage.get("skipped_reason"):
        print(f"Web coverage: skipped — {coverage['skipped_reason']}")
    else:
        print(f"Web coverage: {coverage['checked']} checked, {coverage['cached']} cached, "
              f"{coverage['skipped']} skipped; {len(coverage['outlets'])} outlet(s) already reporting")
        if coverage.get("partial_reason"):
            print(f"Web coverage: PARTIAL — {coverage['partial_reason']}")

    # ── Step 6: Trends, feature pitch, story ideas ──────────────────────────
    print("\nGenerating trends & continuity section...")
    trends_md = ""
    if studies:
        try:
            trends_md = generate_trends_section(
                topic=topic, topic_label=focus_label, digest_content=digest_md,
                outputs_dir=OUTPUTS_DIR, memory_dir=TOPIC_MEMORY_DIR,
                run_date=run_date, api_key=api_key,
                already_reporting=coverage.get("outlets") or set(),
            )
        except llm.ModelDeclined as exc:
            # The digest and the fact check are done; losing the synthesis
            # should not lose them.
            print(f"  WARNING: trends call declined ({exc}); publishing without it.")

    # ── Step 7: Write the run ───────────────────────────────────────────────
    full_md = digest_md.rstrip() + ("\n\n---\n\n" + trends_md + "\n" if trends_md else "\n")
    (OUTPUTS_DIR / f"{stem}.md").write_text(full_md, encoding="utf-8")
    (OUTPUTS_DIR / f"{stem} Fact Check.md").write_text(fact_md, encoding="utf-8")
    record = {
        "schema": 1,
        "model": llm.MODEL,
        "run_date": run_date,
        "days_back": days_back,
        "window_from": window_from,
        "window_to": run_date,
        "focus": focus_label,
        "topic": topic,
        "query": query,
        "journals_searched": len(searchable),
        "journals_not_indexed": not_indexed,
        "screening": counts,
        "primary_audience": primary,
        "secondary_audience": secondary,
        "studies": studies,
        "fact_check": verdicts,
        "coverage": {
            "checked": coverage.get("checked", 0),
            "cached": coverage.get("cached", 0),
            "skipped": coverage.get("skipped", 0),
            "skipped_reason": coverage.get("skipped_reason", ""),
            "partial_reason": coverage.get("partial_reason", ""),
            "by_work": coverage.get("by_work") or {},
        },
        "sections": split_sections(trends_md) if trends_md else {},
    }
    # Written last: screening reads outputs/*.json to know what has been
    # covered, so a record only exists for a run that finished writing.
    (OUTPUTS_DIR / f"{stem}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved outputs/{stem}.md, its fact check and its run record")

    # ── Step 8: Dashboard data ──────────────────────────────────────────────
    print("\nRebuilding dashboard data...")
    rebuild_dashboard_data()
    print("\nDone ✓")


if __name__ == "__main__":
    main()
