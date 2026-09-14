"""Build the static dashboard's JSON from the run records in outputs/.

Every run leaves three files in outputs/: the digest (`<name>.md`), its fact
check (`<name> Fact Check.md`) and the run record (`<name>.json`). The markdown
is for people. This reads only the record, which holds exactly what the model
returned plus what OpenAlex and the coverage check said -- so, unlike
senior-research-digest, there is no regex between the model and the page, and
re-scoring the whole archive is a rebuild with no API calls.

Output is split so the first page load stays flat as runs accumulate:
`docs/data/index.json` holds what the sidebar needs, each run's full body goes
to `docs/data/runs/<id>.json`, and the search text to `docs/data/search.json`,
fetched only once somebody searches.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import factcheck_render
import scoring
import topics

REPO_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
DASHBOARD_DATA_DIR = REPO_ROOT / "docs" / "data"
DASHBOARD_INDEX_PATH = DASHBOARD_DATA_DIR / "index.json"
DASHBOARD_RUNS_DIR = DASHBOARD_DATA_DIR / "runs"
SEARCH_PATH = DASHBOARD_DATA_DIR / "search.json"
HIDDEN_PATH = DASHBOARD_DATA_DIR / "hidden.json"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-") or "untitled"


def is_run_record(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and "run_date" in data and "studies" in data


def _fact_check(record: dict, stem_path: Path) -> dict | None:
    verdicts = record.get("fact_check")
    if verdicts is None:
        return None
    counts = factcheck_render.severity_counts(verdicts)
    revision = sum(1 for v in verdicts
                   if str(v.get("verdict", "")).strip().lower() != "accurate")
    report = stem_path.with_name(stem_path.name + " Fact Check.md")
    return {
        "studies_reviewed": len(verdicts),
        "verdicts_by_work": {
            v.get("work_id", ""): factcheck_render.verdict_line(v.get("verdict"))
            for v in verdicts
        },
        "summary": {
            "total_issues": f"{sum(counts.values())} ({counts['Minor']} Minor, "
                            f"{counts['Moderate']} Moderate, {counts['Major']} Major)",
            "entries_requiring_revision": str(revision),
            "entries_cleared": str(len(verdicts) - revision),
        } if verdicts else None,
        "raw": report.read_text(encoding="utf-8") if report.exists() else "",
    }


def build_run(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    stem = path.with_suffix("")
    run_date = record.get("run_date", "")
    topic = topics.normalize_topic(record.get("topic", ""))

    verdict_records = {v.get("work_id", ""): v for v in (record.get("fact_check") or [])}
    coverage = record.get("coverage") or {}
    by_work = coverage.get("by_work") or {}

    studies = []
    for number, raw in enumerate(record.get("studies") or [], start=1):
        verdict = verdict_records.get(raw.get("work_id", ""))
        cov = by_work.get(raw.get("work_id", "")) or {}
        study = {
            "number": number,
            "title": raw.get("headline", ""),
            "paper_title": raw.get("paper_title", ""),
            "journal": raw.get("journal", ""),
            "published": raw.get("published", ""),
            "work_id": raw.get("work_id", ""),
            "doi": raw.get("doi", ""),
            "source_id": raw.get("source_id", ""),
            "the_study": raw.get("the_study", ""),
            "why_it_matters": raw.get("why_it_matters", ""),
            "story_angle_primary": raw.get("story_angle_primary", ""),
            "story_angle_secondary": raw.get("story_angle_secondary", ""),
            "caveats": raw.get("caveats", ""),
        }
        study.update(scoring.score_study(
            study,
            run_date=run_date,
            coverage_state=cov.get("state") or None,
            verdict=(verdict or {}).get("verdict"),
        ))
        study["verdict"] = factcheck_render.verdict_line(verdict["verdict"]) if verdict else ""
        study["verdict_notes"] = (verdict or {}).get("notes", "")
        study["tags"] = topics.tags_for(
            " ".join([study["title"], study["paper_title"], study["the_study"],
                      study["why_it_matters"]]), topic)
        study["covered_by"] = cov.get("outlets") or []
        study["covered_articles"] = cov.get("articles") or []
        studies.append(study)

    sections = record.get("sections") or {}
    screening = record.get("screening") or {}
    return {
        "id": _slugify(stem.name),
        "filename": stem.name + ".md",
        "title": stem.name,
        "run_date": run_date,
        "coverage_window": f"Last {record.get('days_back', '?')} days",
        "window_from": record.get("window_from", ""),
        "window_to": record.get("window_to", ""),
        "journals_searched": str(record.get("journals_searched", "")),
        "journals_not_indexed": record.get("journals_not_indexed", []),
        "articles_screened": str(screening.get("sent", "")),
        "articles_found": screening.get("found", 0),
        "screening": screening,
        "focus": record.get("focus", ""),
        "topic": topic,
        "is_broad": not topic,
        "primary_audience": record.get("primary_audience", ""),
        "secondary_audience": record.get("secondary_audience", ""),
        "study_count": len(studies),
        "studies": studies,
        "citation_table": [
            {"work_id": s["work_id"], "journal": s["journal"],
             "date": s["published"], "doi": s["doi"]}
            for s in studies
        ],
        "trends_raw": sections.get("trends", ""),
        "feature_pitch_raw": sections.get("feature_pitch", ""),
        "pitch_ideas_raw": sections.get("pitch_ideas", ""),
        "fact_check": _fact_check(record, stem),
        "coverage": {k: coverage.get(k) for k in
                     ("checked", "cached", "skipped", "skipped_reason", "partial_reason")},
    }


def build() -> list[dict]:
    runs = [build_run(p) for p in sorted(OUTPUTS_DIR.glob("*.json")) if is_run_record(p)]
    runs.sort(key=lambda r: (r["run_date"], r["filename"]), reverse=True)
    seen: dict[str, int] = {}
    for run in runs:
        seen[run["id"]] = seen.get(run["id"], 0) + 1
        if seen[run["id"]] > 1:
            run["id"] = f"{run['id']}-{seen[run['id']]}"
    return runs


def _search_blob(run: dict) -> str:
    parts = [run.get("title", ""), run.get("focus", ""), run.get("topic", "")]
    for study in run.get("studies", []):
        parts.extend([study.get("title", ""), study.get("paper_title", ""),
                      study.get("work_id", ""), study.get("doi", ""), study.get("journal", "")])
        parts.extend(study.get("tags") or [])
    return " ".join(p for p in parts if p).lower()


def _index_entry(run: dict) -> dict:
    summary = (run.get("fact_check") or {}).get("summary") or {}
    return {
        "id": run["id"],
        "title": run.get("title", ""),
        "topic": run.get("topic", ""),
        "run_date": run.get("run_date", ""),
        "study_count": run.get("study_count", 0),
        "total_issues": summary.get("total_issues", ""),
        "lead_count": sum(1 for s in run.get("studies", []) if s.get("band") == "Lead"),
        "top_score": max((s.get("score", 0) for s in run.get("studies", [])), default=0),
        "search": _search_blob(run),
    }


def hidden_ids() -> set:
    """Run ids to suppress, from a committed docs/data/hidden.json -- a bad run
    can be hidden with one line while it is sorted out, and nothing is deleted.
    Accepts a bare list or {"ids": [...]}."""
    if not HIDDEN_PATH.exists():
        return set()
    try:
        raw = json.loads(HIDDEN_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"WARNING: {HIDDEN_PATH.name} is unreadable; hiding nothing.")
        return set()
    ids = raw.get("ids", []) if isinstance(raw, dict) else raw
    return {str(i) for i in ids}


def main() -> None:
    runs = build()
    hidden = hidden_ids()
    if hidden:
        kept = [r for r in runs if r["id"] not in hidden]
        print(f"Hiding {len(runs) - len(kept)} run(s) listed in {HIDDEN_PATH.name}")
        runs = kept

    DASHBOARD_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    written = set()
    for run in runs:
        path = DASHBOARD_RUNS_DIR / f"{run['id']}.json"
        path.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
        written.add(path.name)
    stale = [p for p in DASHBOARD_RUNS_DIR.glob("*.json") if p.name not in written]
    for path in stale:
        path.unlink()

    entries = [_index_entry(r) for r in runs]
    SEARCH_PATH.write_text(
        json.dumps({e["id"]: e.pop("search", "") for e in entries}, indent=0, ensure_ascii=False),
        encoding="utf-8")
    index = {
        "generated_from": "outputs/*.json",
        "run_count": len(runs),
        "topics": sorted({r["topic"] for r in runs if r["topic"]}),
        "runs": entries,
    }
    DASHBOARD_INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
    print(f"Wrote {len(runs)} run(s) to {DASHBOARD_RUNS_DIR.relative_to(REPO_ROOT)}/ and "
          f"{DASHBOARD_INDEX_PATH.relative_to(REPO_ROOT)}"
          + (f"; pruned {len(stale)} stale run file(s)" if stale else ""))


if __name__ == "__main__":
    main()
