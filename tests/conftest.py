"""Shared test setup. Nothing here touches a network or an API."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_OUTPUTS = Path(__file__).resolve().parent / "fixtures" / "outputs"

sys.path.insert(0, str(REPO_ROOT / "scripts"))


@pytest.fixture
def built_dashboard(tmp_path, monkeypatch):
    """The dashboard data built from the fixture run into a temp docs/ dir,
    so tests never depend on (or overwrite) the real archive."""
    import build_dashboard_data as bdd

    data = tmp_path / "data"
    monkeypatch.setattr(bdd, "OUTPUTS_DIR", FIXTURE_OUTPUTS)
    monkeypatch.setattr(bdd, "DASHBOARD_DATA_DIR", data)
    monkeypatch.setattr(bdd, "DASHBOARD_INDEX_PATH", data / "index.json")
    monkeypatch.setattr(bdd, "DASHBOARD_RUNS_DIR", data / "runs")
    monkeypatch.setattr(bdd, "SEARCH_PATH", data / "search.json")
    monkeypatch.setattr(bdd, "HIDDEN_PATH", data / "hidden.json")
    monkeypatch.setattr(bdd, "REPO_ROOT", tmp_path)
    data.mkdir()
    bdd.main()
    return tmp_path


class FakeBlock:
    def __init__(self, text, type_="text"):
        self.text = text
        self.type = type_


class FakeResponse:
    def __init__(self, text, stop_reason="end_turn"):
        # A thinking block first, as adaptive thinking produces -- the reason
        # llm.text_of selects by type.
        self.content = [FakeBlock("reasoning", "thinking"), FakeBlock(text)]
        self.stop_reason = stop_reason


class FakeClient:
    """Stands in for anthropic.Anthropic. `answer` maps a request's kwargs to a
    FakeResponse; every call is recorded."""

    def __init__(self, answer):
        self.calls = []
        client = self

        class Messages:
            def create(self, **kwargs):
                client.calls.append(kwargs)
                return answer(kwargs)

        self.messages = Messages()
