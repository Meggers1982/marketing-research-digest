"""Topics, trends parsing, run naming, rendering and coverage -- the pieces
between the API calls."""
import json
from datetime import datetime

import digest_render
import main
import topics
import trends
import web_coverage


# ---------------------------------------------------------------- topics

def test_every_rotation_topic_has_a_query():
    config = json.loads((main.CONFIG_PATH).read_text())
    for topic in config["focus_rotation"]:
        if topic:
            assert topics.normalize_topic(topic) in topics.QUERIES, topic
            assert topics.normalize_topic(topic) in topics.TAG_TERMS, topic


def test_broad_days_search_everything():
    assert topics.query_for("") == ""
    assert topics.label_for("") == "Broad (all marketing topics)"


def test_an_unknown_topic_is_searched_as_a_phrase():
    assert topics.query_for("loot boxes") == '"loot boxes"'


def test_labels_read_properly():
    assert topics.label_for("ai & marketing technology") == "AI & Marketing Technology"
    assert topics.label_for("b2b & sales") == "B2B & Sales"


def test_tags_carry_the_run_topic_and_what_the_text_is_about():
    tags = topics.tags_for("Influencer posts on TikTok raised prices", "branding")
    assert {"branding", "social media & influencers", "pricing & promotions"} <= set(tags)


# ----------------------------------------------------------------- focus

def test_the_dispatch_override_wins(monkeypatch):
    monkeypatch.setenv("DIGEST_FOCUS", "advertising")
    assert main.pick_subject_focus({"subject_focus": "branding"}, datetime(2026, 9, 14)) == "advertising"


def test_the_rotation_moves_by_day(monkeypatch):
    monkeypatch.delenv("DIGEST_FOCUS", raising=False)
    config = {"focus_rotation": ["", "a", "b"]}
    day1 = main.pick_subject_focus(config, datetime(2026, 9, 14))
    day2 = main.pick_subject_focus(config, datetime(2026, 9, 15))
    assert day1 != day2


def test_a_second_run_the_same_day_does_not_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUTS_DIR", tmp_path)
    stem = main.digest_stem("Branding", "2026-09-14")
    assert main.unique_stem(stem) == stem
    (tmp_path / f"{stem}.json").write_text("{}")
    assert main.unique_stem(stem) == f"{stem} (Part 2)"


# ----------------------------------------------------------------- trends

BODY = """## Research Trends & Continuity

_No prior digest._

## Bigger Picture: Feature Pitch

**The pattern:** W1 and W2.

## Story Ideas by Study

- **H (Work ID W1):** angle, for a trade brief.

```topic_memory
## Established findings
- one
```"""


def test_the_memory_block_is_split_off_and_the_sections_parsed():
    visible, memory = trends.extract_memory(BODY)
    assert "topic_memory" not in visible
    assert memory.startswith("## Established findings")
    sections = trends.split_sections(visible)
    assert sections["trends"] == "_No prior digest._"
    assert sections["feature_pitch"].startswith("**The pattern:**")
    assert "Work ID W1" in sections["pitch_ideas"]


def test_a_truncated_response_leaves_memory_alone():
    _, memory = trends.extract_memory("## Research Trends & Continuity\n\ncut off")
    assert memory is None


def test_the_previous_digest_is_the_latest_earlier_one_on_the_topic(tmp_path):
    for name, topic, date in (("a", "branding", "2026-09-01"), ("b", "branding", "2026-09-10"),
                              ("c", "advertising", "2026-09-12"), ("d", "branding", "2026-09-14")):
        (tmp_path / f"{name}.json").write_text(json.dumps({"topic": topic, "run_date": date,
                                                           "studies": []}))
        (tmp_path / f"{name}.md").write_text(name)
    assert trends.find_previous_digest("Branding", tmp_path, before="2026-09-14") == "b"
    assert trends.find_previous_digest("", tmp_path) is None


def test_memory_files_are_named_by_topic():
    assert trends.slugify("") == "broad"
    assert trends.slugify("Food, Health & Wellbeing") == "food-health-wellbeing"


# ----------------------------------------------------------------- render

def test_the_digest_renders_one_entry_per_record_and_a_citation_table():
    records = [{"headline": "H|1", "journal": "J", "published": "2026-09-01", "work_id": "W1",
                "doi": "", "the_study": "S", "why_it_matters": "M",
                "story_angle_primary": "P", "story_angle_secondary": "Q", "caveats": ""}]
    md = digest_render.render_digest(records, "marketers", "general readers")
    assert "### 1. H/1" in md                     # a pipe would break the table
    assert "- **For marketers:** P" in md
    assert "- **For general readers:** Q" in md
    assert "**Caveats:** None significant" in md
    assert "| 1 | W1 | J | 2026-09-01 | Not available |" in md


# --------------------------------------------------------------- coverage

def test_coverage_without_a_key_says_it_did_not_look(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    result = web_coverage.check_digest([("W1", "Free shipping thresholds")])
    assert result["checked"] == 0
    assert result["skipped_reason"] == "SERPAPI_API_KEY is not set"
    assert result["by_work"] == {}


def test_headline_matching_needs_real_overlap():
    assert web_coverage.title_similar(
        "Free shipping thresholds make shoppers buy more",
        "Why free shipping thresholds make shoppers buy more, study finds")
    assert not web_coverage.title_similar(
        "Free shipping thresholds make shoppers buy more",
        "Retail sales rose in August")
