import scoring


def test_the_evidence_ladder_is_marketings():
    cases = {
        "A field experiment with a grocery chain": "field experiment",
        "We analyze 2.4 million transactions from a retailer": "behavioral data",
        "Across five online experiments with Prolific participants": "experiments",
        "A survey of 412 respondents analyzed with PLS-SEM": "survey",
        "In-depth interviews with 22 brand managers": "qualitative",
        "A bibliometric review of the influencer literature": "review",
        "A meta-analysis of 212 effect sizes": "meta-analysis",
    }
    for text, label in cases.items():
        assert scoring.evidence_type(text)[0] == label, text


def test_an_unstated_design_is_neutral():
    assert scoring.evidence_type("Researchers found a link.") == ("unspecified", 2)


def test_a_field_experiment_outranks_a_survey():
    assert scoring.evidence_type("field experiment")[1] > scoring.evidence_type("survey")[1]


def test_sample_size_reads_the_forms_write_ups_use():
    assert scoring.sample_size("N = 1,204 shoppers")[0] == 1204
    assert scoring.sample_size("data from 48,200 customers")[0] == 48200
    assert scoring.sample_size("3.1 million users")[0] == 3_100_000
    assert scoring.sample_size("no numbers here") == (None, 2)


def test_recency_reads_iso_dates():
    assert scoring.recency("2026-09-02", "2026-09-14") == 5
    assert scoring.recency("2026-05-02", "2026-09-14") == 3
    assert scoring.recency("", "2026-09-14") == 0
    assert scoring.recency("2026-11-01", "2026-09-14") == 5   # issue date ahead


def test_an_unmeasured_component_is_dropped_not_guessed():
    assert scoring.story_score({"evidence_type": 5, "coverage_gap": None}) == 100


def test_an_unchecked_study_cannot_be_a_lead():
    study = {"the_study": "A field experiment with 48,200 customers.",
             "journal": "Journal of Marketing Research", "published": "2026-09-10"}
    unchecked = scoring.score_study(study, run_date="2026-09-14", verdict="accurate")
    assert unchecked["score"] >= 82
    assert unchecked["band"] == "Strong"
    checked = scoring.score_study(study, run_date="2026-09-14",
                                  coverage_state="unreported", verdict="accurate")
    assert checked["band"] == "Lead"


def test_verdicts_are_the_records_words():
    assert scoring.accuracy("accurate") == 5
    assert scoring.accuracy("significant") == 0
    assert scoring.accuracy(None) is None


def test_journal_tier_uses_the_ratings():
    top = scoring.score_study({"journal": "Journal of Marketing"}, run_date="2026-09-14")
    assert top["journal_tier"] == "A*"
    assert top["components"]["journal_tier"] == 5
