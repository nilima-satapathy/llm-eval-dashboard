"""Light checks that dashboard dependencies and store integration work."""

from __future__ import annotations

from pathlib import Path

from src.metrics_store import MetricsStore
from src.runners import run_evaluation


def test_dashboard_can_read_runs_after_eval(tmp_path: Path):
    """Same data path the Streamlit app uses (injected store for isolation)."""
    db = tmp_path / "dash.sqlite3"
    store = MetricsStore(db_path=db)
    out = run_evaluation(
        backend="golden",
        case_ids=["qa-001", "qa-002"],
        store=store,
        export_csv=False,
        notes="dashboard-helper-test",
    )
    runs = store.list_runs()
    assert len(runs) >= 1
    latest = store.latest_run()
    assert latest is not None
    assert latest["run_id"] == out["summary"]["run_id"]
    assert float(latest["pass_rate"]) == 1.0
    results = store.results_for_run(latest["run_id"])
    assert len(results) == 2


def test_streamlit_importable():
    import streamlit  # noqa: F401

    assert streamlit is not None
