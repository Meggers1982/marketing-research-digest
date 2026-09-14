"""The dashboard is plain JS reading JSON that Python writes.

Nothing but these tests connects the two, so a renamed field would fail
silently in the browser rather than in CI. Three layers, lifted from
senior-research-digest (which lifted them from agingwire): what the builder
writes, a contract check that reads the inline script as text, and a render
check that actually executes it in Node against the fixture run -- because
reading the source cannot catch a ReferenceError.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import build_dashboard_data as bdd
from conftest import FIXTURE_OUTPUTS, REPO_ROOT

DASHBOARD = REPO_ROOT / "docs" / "index.html"
HARNESS = Path(__file__).with_name("dashboard_harness.mjs")
NODE = shutil.which("node")


def dashboard_html() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def dashboard_js() -> str:
    match = re.search(r'<script id="app">(.*?)</script>', dashboard_html(), re.S)
    assert match, "dashboard has no inline script"
    return match.group(1)


def js_function(name: str) -> str:
    js = dashboard_js()
    start = js.index(f"function {name}(")
    return js[start:js.index("\n}", start)]


def _top_level_items(source: str) -> list:
    items, depth, quote, current = [], 0, None, ""
    for char in source:
        if quote:
            current += char
            if char == quote:
                quote = None
            continue
        if char in "\"'`":
            quote, current = char, current + char
        elif char in "([{":
            depth, current = depth + 1, current + char
        elif char in ")]}":
            depth, current = depth - 1, current + char
        elif char == "," and depth == 0:
            items.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        items.append(current)
    return [i for i in items if i.strip()]


@pytest.fixture
def run_doc(monkeypatch):
    monkeypatch.setattr(bdd, "OUTPUTS_DIR", FIXTURE_OUTPUTS)
    runs = bdd.build()
    assert runs, "no fixture run"
    return runs[0]


# ------------------------------------------------------------------ builder

def test_the_builder_reads_the_run_record(run_doc):
    assert run_doc["study_count"] == 2
    assert run_doc["articles_found"] == 215
    first, second = run_doc["studies"]
    assert first["work_id"] == "W9000000001"
    assert first["verdict"] == "✅ Accurate"
    assert first["coverage_state"] == "unreported"
    assert first["evidence_type"] == "field experiment"
    assert first["band"] == "Lead"
    assert second["verdict"] == "⚠️ Minor issues"
    assert second["covered_by"] == ["Marketing Dive"]
    assert second["evidence_type"] == "survey"
    assert run_doc["fact_check"]["summary"]["entries_requiring_revision"] == "1"
    assert run_doc["feature_pitch_raw"].startswith("**The pattern:**")
    assert run_doc["citation_table"][1]["doi"] == ""


def test_the_builder_writes_index_runs_and_search(built_dashboard):
    data = built_dashboard / "data"
    index = json.loads((data / "index.json").read_text())
    assert index["run_count"] == 1
    assert index["topics"] == ["pricing & promotions"]
    entry = index["runs"][0]
    assert "search" not in entry, "search blobs belong in search.json"
    assert (data / "runs" / f"{entry['id']}.json").exists()
    assert "w9000000001" in json.loads((data / "search.json").read_text())[entry["id"]]


def test_a_hidden_run_is_left_out(tmp_path, monkeypatch):
    hidden = tmp_path / "hidden.json"
    monkeypatch.setattr(bdd, "HIDDEN_PATH", hidden)
    hidden.write_text(json.dumps({"ids": ["x"]}))
    assert bdd.hidden_ids() == {"x"}
    hidden.write_text("not json")
    assert bdd.hidden_ids() == set()


def test_the_real_index_exists_so_the_page_can_load():
    assert (REPO_ROOT / "docs" / "data" / "index.json").exists()


# ----------------------------------------------------------------- contract

def test_every_run_field_the_dashboard_reads_exists(run_doc):
    used = set(re.findall(r"\brun\.([a-z_]+)", dashboard_js()))
    assert used
    assert sorted(f for f in used if f not in run_doc) == []


def test_every_study_field_the_card_reads_exists(run_doc):
    used = set(re.findall(r"\bstudy\.([a-z_0-9]+)", js_function("renderStudy")))
    assert used
    assert sorted(f for f in used if f not in run_doc["studies"][0]) == []


def test_every_index_field_the_sidebar_reads_exists(run_doc):
    entry = bdd._index_entry(run_doc)
    used = set(re.findall(r"\br\.([a-z_]+)", js_function("renderSidebar")))
    assert used
    assert sorted(f for f in used if f not in entry) == []


def test_the_csv_header_and_rows_stay_aligned():
    source = js_function("exportRunToCsv")
    names = re.findall(r'"([a-z_]+)"', re.search(r"const header = \[(.*?)\];", source, re.S).group(1))
    assert len(names) == len(set(names))
    rows = re.search(r"const rows = exportedStudies\(run\)\.map\(s => \[(.*?)\]\);", source, re.S).group(1)
    assert len(names) == len(_top_level_items(rows))


def test_status_is_keyed_on_the_work_id_everywhere():
    js = dashboard_js()
    assert "pmid" not in js.lower()
    assert 'header.indexOf("work_id")' in js
    assert '"work_id"' in js_function("exportRunToCsv")


def test_both_exports_follow_the_filters_on_screen():
    assert "run.studies.filter(matchesFacets)" in js_function("exportedStudies")
    for fn in ("exportRunToCsv", "exportRunToDocx"):
        assert "exportedStudies(run)" in js_function(fn), fn


def test_every_jump_target_is_a_real_section():
    js = dashboard_js()
    targets = set(re.findall(r'\["([a-z-]+)", "[A-Z]', js))
    built = set(re.findall(r'sectionBlock\("([a-z-]+)"', js))
    assert built and targets - built == set()


def test_the_pitch_comes_before_the_studies():
    js = dashboard_js()
    body = js[js.index("main.innerHTML = `\n    <div class=\"run-header\">"):]
    assert body.index("${pitchHtml}") < body.index("${studiesHtml}")


def test_the_theme_is_settled_before_the_first_paint():
    head = dashboard_html().split("</head>")[0]
    assert "dataset.theme" in head
    assert "mrd-theme" in head


def test_the_docx_library_is_vendored():
    assert (REPO_ROOT / "docs" / "vendor" / "docx-8.5.0.umd.js").exists()
    assert "vendor/docx-8.5.0.umd.js" in dashboard_js()


# ------------------------------------------------------------------- render

def _render(html: str, data_root: Path) -> str:
    script = re.search(r'<script id="app">(.*?)</script>', html, re.S).group(1)
    work = data_root / "harness"
    work.mkdir(exist_ok=True)
    (work / "script.js").write_text(script, encoding="utf-8")
    (work / "page.html").write_text(html, encoding="utf-8")
    result = subprocess.run(
        [NODE, str(HARNESS), str(work / "script.js"), str(work / "page.html"), str(data_root)],
        capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise AssertionError(result.stderr.strip() or "render failed")
    return result.stdout


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_the_page_renders_the_run(built_dashboard):
    out = _render(dashboard_html(), built_dashboard)
    for section in ("feature-pitch", "pitch-ideas", "studies", "limits"):
        assert f'id="{section}"' in out, section
    assert "band-chip" in out and "score-chip" in out
    assert "https://doi.org/10.0000/fixture.1" in out
    assert "https://openalex.org/W9000000001" in out
    assert "For marketers and brand leaders:" in out
    assert "The model saw 40 of 215 articles" in out
    assert 'data-facet="band"' in out


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_the_empty_archive_explains_itself(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "index.json").write_text(json.dumps(
        {"run_count": 0, "topics": [], "runs": []}))
    assert "No digests yet" in _render(dashboard_html(), tmp_path)


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_a_reference_error_would_fail_the_render(built_dashboard):
    broken = dashboard_html().replace(
        "function renderStudy(", "function renderStudy(){ return nope.missing; }\nfunction _unused(", 1)
    with pytest.raises(AssertionError):
        _render(broken, built_dashboard)
