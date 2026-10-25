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


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FakeClient:
    """Stands in for anthropic.Anthropic. `answer` maps a request's kwargs to a
    FakeResponse; every call is recorded, whether it went live (`live_calls`)
    or through the Batch API (`batches_created`, one list of params per batch).

    A batch ends on its first `retrieve` unless `batch_never_ends` is set.
    `batch_result_type` overrides the result type (e.g. "errored")."""

    def __init__(self, answer, batch_never_ends=False, batch_result_type="succeeded"):
        self.calls = []
        self.live_calls = []
        self.batches_created = []
        self.canceled = []
        client = self
        stored = {}

        class Batches:
            def create(self, requests):
                batch_id = f"msgbatch_{len(stored)}"
                stored[batch_id] = requests
                client.batches_created.append([r["params"] for r in requests])
                return _Obj(id=batch_id, processing_status="in_progress")

            def retrieve(self, batch_id):
                ended = not batch_never_ends or batch_id in client.canceled
                return _Obj(id=batch_id,
                            processing_status="ended" if ended else "in_progress")

            def cancel(self, batch_id):
                client.canceled.append(batch_id)
                return _Obj(id=batch_id, processing_status="canceling")

            def results(self, batch_id):
                if batch_id in client.canceled:
                    return
                for r in stored[batch_id]:
                    client.calls.append(r["params"])
                    message = answer(r["params"]) if batch_result_type == "succeeded" else None
                    yield _Obj(custom_id=r["custom_id"],
                               result=_Obj(type=batch_result_type, message=message))

        class Messages:
            batches = Batches()

            def create(self, **kwargs):
                client.calls.append(kwargs)
                client.live_calls.append(kwargs)
                return answer(kwargs)

        self.messages = Messages()


@pytest.fixture(autouse=True)
def no_batch_polling_delay(monkeypatch):
    import llm
    monkeypatch.setattr(llm, "BATCH_POLL_SECONDS", 0)
