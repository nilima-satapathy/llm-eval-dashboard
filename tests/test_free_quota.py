"""Tests for free-tier usage tracking and capacity advice."""

from __future__ import annotations

from pathlib import Path

from src.free_quota import (
    FreeTierConfig,
    UsageWindow,
    build_quota_snapshot,
    capacity_from_usage,
    usage_status,
)
from src.metrics_store import CaseResult, MetricsStore, RunSummary


def test_usage_status_thresholds():
    assert usage_status(10, 10)[0] == "ok"
    assert usage_status(75, 10)[0] == "caution"
    assert usage_status(10, 95)[0] == "critical"


def test_capacity_from_usage_math():
    cfg = FreeTierConfig(
        provider="groq",
        daily_requests=100,
        daily_tokens=10_000,
        rpm=30,
        tpm=6_000,
        monthly_usd=None,
        model_hint="llama-3.1-8b-instant",
    )
    today = UsageWindow(
        label="today_utc",
        since_iso="2026-07-16T00:00:00+00:00",
        requests=16,
        tokens=800,
        runs=2,
        estimated_cost_usd=0.0,
    )
    advice = capacity_from_usage(
        today=today,
        config=cfg,
        avg_tokens_per_case=50.0,
        full_suite_cases=42,
        quick_suite_cases=4,
    )
    assert advice.remaining_requests_today == 84
    assert advice.remaining_tokens_today == 9_200
    assert advice.full_runs_left_by_requests == 2
    assert advice.quick_runs_left_by_requests == 21
    assert advice.full_runs_left_by_tokens == 4
    assert advice.status == "ok"


def test_capacity_clamps_at_zero_when_over_budget():
    cfg = FreeTierConfig(
        provider="groq",
        daily_requests=10,
        daily_tokens=100,
        rpm=30,
        tpm=6_000,
        monthly_usd=None,
        model_hint="x",
    )
    today = UsageWindow(
        label="today_utc",
        since_iso="2026-07-16T00:00:00+00:00",
        requests=50,
        tokens=500,
        runs=5,
        estimated_cost_usd=0.0,
    )
    advice = capacity_from_usage(
        today=today, config=cfg, avg_tokens_per_case=10.0, full_suite_cases=42
    )
    assert advice.remaining_requests_today == 0
    assert advice.remaining_tokens_today == 0
    assert advice.status == "critical"


def test_store_usage_and_snapshot(tmp_path: Path):
    db = tmp_path / "usage.sqlite3"
    store = MetricsStore(db_path=db)
    summary = RunSummary(
        run_id="abc123def456",
        started_at="2026-07-16T10:00:00+00:00",
        finished_at="2026-07-16T10:01:00+00:00",
        backend="openai",
        model="llama-3.1-8b-instant",
        total_cases=2,
        passed=1,
        failed=1,
        pass_rate=0.5,
        avg_latency_ms=100.0,
        p95_latency_ms=120.0,
        total_tokens=400,
        estimated_cost_usd=0.0001,
        notes="usage-test",
    )
    results = [
        CaseResult(
            case_id="qa-001",
            question="q1",
            answer="a1",
            passed=True,
            must_include_score=1.0,
            reference_overlap_score=1.0,
            latency_ms=90.0,
            total_tokens=150,
            estimated_cost_usd=0.00005,
            model="llama-3.1-8b-instant",
            backend="openai",
        ),
        CaseResult(
            case_id="qa-002",
            question="q2",
            answer="a2",
            passed=False,
            must_include_score=0.2,
            reference_overlap_score=0.2,
            latency_ms=110.0,
            total_tokens=250,
            estimated_cost_usd=0.00005,
            model="llama-3.1-8b-instant",
            backend="openai",
        ),
    ]
    store.save_run(summary, results)

    golden_sum = RunSummary(
        run_id="golden000001",
        started_at="2026-07-16T11:00:00+00:00",
        finished_at="2026-07-16T11:01:00+00:00",
        backend="golden",
        model="golden",
        total_cases=1,
        passed=1,
        failed=0,
        pass_rate=1.0,
        avg_latency_ms=1.0,
        p95_latency_ms=1.0,
        total_tokens=None,
        estimated_cost_usd=None,
    )
    store.save_run(
        golden_sum,
        [
            CaseResult(
                case_id="qa-001",
                question="q",
                answer="a",
                passed=True,
                must_include_score=1.0,
                reference_overlap_score=1.0,
                latency_ms=1.0,
                backend="golden",
            )
        ],
    )

    usage = store.usage_for_backend(backend="openai", since_iso="2026-07-01T00:00:00")
    assert usage["requests"] == 2
    assert usage["tokens"] == 400
    assert usage["runs"] == 1

    avg = store.avg_tokens_per_case(backend="openai")
    assert avg == 200.0

    snap = build_quota_snapshot(store)
    assert "today" in snap
    assert "advice" in snap
    assert snap["config"].provider
