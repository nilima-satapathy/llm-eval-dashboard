"""Integration tests for quality-gate orchestration."""

from __future__ import annotations

from pathlib import Path

from gate.run_gate import run_quality_gate
from src.metrics_store import MetricsStore


def test_gate_pr_profile_green_offline(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "gate.sqlite3")
    # Point reports to tmp by monkeypatching write path via env-free approach:
    # run_quality_gate uses default reports dir — fine for CI; use soft path check
    code, payload = run_quality_gate(
        profile="pr",
        store=store,
        export_csv=False,
    )
    assert code == 0, payload
    assert payload["ok"] is True
    decision = payload["decision"]
    assert decision.ok is True
    assert len(decision.suite_results) == 2
    assert all(r.ok for r in decision.suite_results)
    assert Path(payload["reports"]["md"]).exists()


def test_gate_mock_backend_fails(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "gate_fail.sqlite3")
    code, payload = run_quality_gate(
        profile="pr",
        store=store,
        backend_override="mock",
        export_csv=False,
    )
    assert code == 1
    assert payload["ok"] is False
    decision = payload["decision"]
    assert decision.exit_code == 1
    # quality suite should fail under mock
    quality = next(r for r in decision.suite_results if r.name == "quality")
    assert quality.ok is False
