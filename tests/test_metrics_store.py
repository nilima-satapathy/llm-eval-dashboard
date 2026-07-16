"""M5: metrics store + runner persistence."""

from __future__ import annotations

from pathlib import Path

from src.metrics_store import MetricsStore
from src.runners import run_evaluation


def test_run_evaluation_persists_sqlite_and_csv(tmp_path: Path):
    db = tmp_path / "test_runs.sqlite3"
    store = MetricsStore(db_path=db)
    out = run_evaluation(
        backend="golden",
        case_ids=["qa-001", "qa-002", "qa-004"],
        store=store,
        notes="m5-unit-test",
        export_csv=True,
    )
    summary = out["summary"]
    assert summary["total_cases"] == 3
    assert summary["passed"] == 3
    assert summary["pass_rate"] == 1.0
    assert summary["avg_latency_ms"] >= 0
    assert summary["p95_latency_ms"] >= 0
    assert out["db_path"] == str(db)

    loaded = store.get_run(summary["run_id"])
    assert loaded is not None
    assert "m5-unit-test" in loaded["notes"]
    assert "suite=golden" in loaded["notes"]

    rows = store.results_for_run(summary["run_id"])
    assert len(rows) == 3
    assert all(r["passed"] == 1 for r in rows)
    assert all(r["latency_ms"] is not None for r in rows)

    csv_path = Path(out["csv_path"])
    assert csv_path.exists()
    text = csv_path.read_text(encoding="utf-8")
    assert "qa-001" in text
    assert "must_include_score" in text


def test_compare_last_two_runs(tmp_path: Path):
    db = tmp_path / "cmp.sqlite3"
    store = MetricsStore(db_path=db)
    run_evaluation(
        backend="golden",
        case_ids=["qa-001", "qa-002"],
        store=store,
        export_csv=False,
    )
    run_evaluation(
        backend="golden",
        case_ids=["qa-001", "qa-002"],
        store=store,
        export_csv=False,
    )
    cmp = store.compare_last_two()
    assert cmp is not None
    assert cmp["pass_rate_delta"] == 0.0
    assert len(store.list_runs()) >= 2


def test_latest_run_after_eval(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "latest.sqlite3")
    out = run_evaluation(
        backend="golden",
        case_ids=["qa-001"],
        store=store,
        export_csv=False,
    )
    latest = store.latest_run()
    assert latest is not None
    assert latest["run_id"] == out["summary"]["run_id"]
