"""Ship-gate tests for dashboard data helpers and free-token bar math."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from dashboard import app as dash
from src.free_quota import build_quota_snapshot
from src.metrics_store import CaseResult, MetricsStore, RunSummary
from src.runners import run_evaluation


def test_runs_df_empty_store(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "empty.sqlite3")
    df = dash.runs_df(store)
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_runs_df_sorted_chronologically(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "runs.sqlite3")
    run_evaluation(
        backend="golden",
        case_ids=["qa-001"],
        store=store,
        export_csv=False,
        notes="first",
    )
    run_evaluation(
        backend="golden",
        case_ids=["qa-002"],
        store=store,
        export_csv=False,
        notes="second",
    )
    df = dash.runs_df(store)
    assert len(df) >= 2
    assert list(df["finished_at"]) == sorted(df["finished_at"])


def test_results_df_empty_unknown_run(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "r.sqlite3")
    df = dash.results_df(store, "no-such-run")
    assert df.empty


def test_results_df_after_eval(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "r2.sqlite3")
    out = run_evaluation(
        backend="golden",
        case_ids=["qa-001", "qa-002"],
        store=store,
        export_csv=False,
    )
    rid = out["summary"]["run_id"]
    df = dash.results_df(store, rid)
    assert len(df) == 2
    assert set(df["case_id"]) == {"qa-001", "qa-002"}
    assert "must_include_score" in df.columns
    assert "passed" in df.columns


def test_dashboard_failure_filter_logic(tmp_path: Path):
    """Mirrors dashboard: failed = res[res['passed'] == 0]."""
    store = MetricsStore(db_path=tmp_path / "fail.sqlite3")
    out = run_evaluation(
        backend="mock",
        case_ids=["qa-001", "qa-002"],
        store=store,
        export_csv=False,
    )
    res = dash.results_df(store, out["summary"]["run_id"])
    failed = res[res["passed"] == 0]
    assert len(failed) >= 1
    # KPI-style fields used by main page
    latest = store.latest_run()
    assert latest is not None
    assert 0.0 <= float(latest["pass_rate"]) <= 1.0


def test_free_tokens_bar_full_when_no_openai_usage(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FREE_TIER_DAILY_TOKENS", "1000")
    store = MetricsStore(db_path=tmp_path / "q.sqlite3")
    # golden usage must not consume free tokens bar
    run_evaluation(
        backend="golden",
        case_ids=["qa-001"],
        store=store,
        export_csv=False,
    )
    snap = build_quota_snapshot(store)
    remaining = snap["advice"].remaining_tokens_today
    limit = snap["config"].daily_tokens
    assert remaining == limit
    frac_left = min(1.0, remaining / max(1, limit))
    assert frac_left == 1.0


def test_free_tokens_bar_decreases_with_openai_usage(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FREE_TIER_DAILY_TOKENS", "1000")
    store = MetricsStore(db_path=tmp_path / "q2.sqlite3")
    summary = RunSummary(
        run_id="tokrun000001",
        started_at="2099-01-01T00:00:00+00:00",
        finished_at="2099-01-01T00:01:00+00:00",
        backend="openai",
        model="llama-3.1-8b-instant",
        total_cases=1,
        passed=1,
        failed=0,
        pass_rate=1.0,
        avg_latency_ms=10.0,
        p95_latency_ms=10.0,
        total_tokens=250,
        estimated_cost_usd=0.0,
    )
    # finished_at far future so "today" filter may exclude — use current window
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    summary.started_at = now
    summary.finished_at = now
    store.save_run(
        summary,
        [
            CaseResult(
                case_id="qa-001",
                question="q",
                answer="a",
                passed=True,
                must_include_score=1.0,
                reference_overlap_score=1.0,
                latency_ms=10.0,
                total_tokens=250,
                backend="openai",
                model="llama-3.1-8b-instant",
            )
        ],
    )
    snap = build_quota_snapshot(store)
    assert snap["today"].tokens == 250
    remaining = snap["advice"].remaining_tokens_today
    assert remaining == 750
    frac_left = remaining / 1000
    assert 0.74 < frac_left < 0.76


def test_render_free_tokens_bar_calls_streamlit(tmp_path: Path, monkeypatch):
    store = MetricsStore(db_path=tmp_path / "ui.sqlite3")
    caption = MagicMock()
    progress = MagicMock()
    monkeypatch.setattr(dash.st, "caption", caption)
    monkeypatch.setattr(dash.st, "progress", progress)
    dash.render_free_tokens_bar(store)
    assert caption.call_count >= 1
    assert "Free cloud quota" in caption.call_args_list[0].args[0]
    progress.assert_called_once()
    args, kwargs = progress.call_args
    assert args[0] == pytest.approx(1.0)
    assert "text" in kwargs
    assert "tokens left" in kwargs["text"]
    assert "resets daily" in kwargs["text"]


def test_compare_last_two_none_with_single_run(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "one.sqlite3")
    run_evaluation(
        backend="golden", case_ids=["qa-001"], store=store, export_csv=False
    )
    assert store.compare_last_two() is None


def test_export_csv_missing_run_raises(tmp_path: Path):
    store = MetricsStore(db_path=tmp_path / "csv.sqlite3")
    with pytest.raises(ValueError):
        store.export_run_csv("missing")
