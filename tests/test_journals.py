import journals


def test_issns_survive_what_a_spreadsheet_does_to_them():
    assert journals.normalize_issn("0022-2429") == "0022-2429"
    assert journals.normalize_issn("09732586") == "0973-2586"
    assert journals.normalize_issn("9732594") == "0973-2594"
    assert journals.normalize_issn("1234-567x") == "1234-567X"


def test_placeholders_are_not_issns():
    for raw in ("", "unverified", "n/a", "N/A (online only)", "-"):
        assert journals.normalize_issn(raw) == "", raw


def test_ceased_and_dormant_titles_are_not_searched():
    active_names = {j.name for j in journals.active()}
    everything = journals.load()
    inactive = [j for j in everything if not j.active]
    assert inactive, "the list carries 19 dead titles; none were recognized"
    assert all(j.name not in active_names for j in inactive)
    assert "Journal of Direct Marketing" not in active_names


def test_most_active_journals_resolve_to_an_openalex_source():
    """177 of 189 resolved on 2026-09-14. A big drop means the CSV lost its
    source-ID column (re-run resolve_sources.py), not that journals vanished."""
    assert len(journals.searchable()) >= 170


def test_tier_comes_from_the_lists_own_ratings():
    jmr = journals.find("Journal of Marketing Research")
    assert journals.tier_points(jmr) == ("A*", 5)
    assert journals.tier_points(journals.find("Journal of Consumer Marketing"))[1] == 4
    assert journals.tier_points(None) == ("unknown", 3)


def test_unrated_is_neutral_not_a_penalty():
    hbr = journals.find("Harvard Business Review")
    assert hbr is not None
    assert journals.tier_points(hbr) == ("unrated", 3)


def test_find_tolerates_case_and_a_leading_the():
    assert journals.find("the journal of marketing") is not None
    assert journals.find("JOURNAL OF MARKETING").name == "Journal of Marketing"
