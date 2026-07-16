"""Ship-gate tests for evaluation runner behaviour."""

from __future__ import annotations

from pathlib import Path

from src.runners import evaluate_case, run_evaluation
from src.metrics_store import MetricsStore
from src.target_app import GoldenTarget, MockTarget


def test_evaluate_case_golden_passes_seed():
    case = {
        "id": "qa-001",
        "question": None,  # filled below
        "must_include": [],
        "must_not_include": [],
        "reference_answer": "",
    }
    from src.dataset import get_case

    real = get_case("qa-001")
    target = GoldenTarget()
    result = evaluate_case(real, target)
    assert result.passed is True
    assert result.error is None
    assert result.must_include_score >= 0.7
    assert result.reference_overlap_score >= 0.85
    assert result.latency_ms >= 0


def test_evaluate_case_mock_typically_fails_metrics():
    from src.dataset import get_case

    case = get_case("qa-001")
    result = evaluate_case(case, MockTarget())
    # Mock placeholder rarely matches must_include / reference
    assert result.passed is False
    assert result.error is None
    assert result.answer


def test_evaluate_case_records_sut_exception():
    class Boom:
        name = "boom"

        def complete(self, prompt: str):
            raise RuntimeError("simulated outage")

    from src.dataset import get_case

    result = evaluate_case(get_case("qa-001"), Boom())  # type: ignore[arg-type]
    assert result.passed is False
    assert result.error is not None
    assert "simulated outage" in result.error
    assert result.answer == ""


def test_run_evaluation_full_golden_suite(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "full.sqlite3")
    out = run_evaluation(
        backend="golden",
        store=store,
        notes="ship-full-golden",
        export_csv=True,
    )
    s = out["summary"]
    assert s["total_cases"] >= 40
    assert s["passed"] == s["total_cases"]
    assert s["pass_rate"] == 1.0
    assert s["failed"] == 0
    assert not out["failed_case_ids"]
    assert Path(out["csv_path"]).exists()


def test_run_evaluation_quick_subset_matches_dashboard(tmp_path: Path):
    """Dashboard Quick run uses these four seed ids."""
    store = MetricsStore(db_path=tmp_path / "quick.sqlite3")
    ids = ["qa-001", "qa-002", "qa-004", "qa-007"]
    out = run_evaluation(
        backend="golden",
        case_ids=ids,
        store=store,
        notes="dashboard-trigger",
        export_csv=False,
    )
    assert out["summary"]["total_cases"] == 4
    assert out["summary"]["pass_rate"] == 1.0
    assert out["summary"]["notes"] == "dashboard-trigger"
    assert out["summary"]["backend"] == "golden"


def test_explicit_backend_not_overridden_by_env(tmp_path: Path, monkeypatch):
    """Regression: .env TARGET_BACKEND=openai must not relabel a golden run."""
    monkeypatch.setenv("TARGET_BACKEND", "openai")
    store = MetricsStore(db_path=tmp_path / "label.sqlite3")
    out = run_evaluation(
        backend="golden",
        case_ids=["qa-001"],
        store=store,
        export_csv=False,
    )
    assert out["summary"]["backend"] == "golden"


def test_run_evaluation_mock_has_failures(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "mock.sqlite3")
    out = run_evaluation(
        backend="mock",
        case_ids=["qa-001", "qa-002"],
        store=store,
        export_csv=False,
    )
    assert out["summary"]["total_cases"] == 2
    assert out["summary"]["passed"] < 2
    assert out["failed_case_ids"]


def test_run_evaluation_unknown_id_subset_emptyish(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "empty.sqlite3")
    out = run_evaluation(
        backend="golden",
        case_ids=["qa-does-not-exist"],
        store=store,
        export_csv=False,
    )
    assert out["summary"]["total_cases"] == 0
    assert out["summary"]["pass_rate"] == 0.0
