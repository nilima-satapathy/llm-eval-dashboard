"""Pure unit tests for gate decision logic."""

from __future__ import annotations

from gate.decide import (
    decide_gate,
    evaluate_baseline_drop,
    evaluate_suite_summary,
)


def test_suite_pass_when_thresholds_met():
    r = evaluate_suite_summary(
        name="quality",
        backend="golden",
        suite="golden",
        summary={
            "run_id": "abc",
            "total_cases": 4,
            "passed": 4,
            "pass_rate": 1.0,
            "avg_latency_ms": 10.0,
        },
        failed_case_ids=[],
        min_pass_rate=1.0,
        max_avg_latency_ms=5000,
    )
    assert r.ok is True
    assert r.reasons == []


def test_suite_fail_on_pass_rate():
    r = evaluate_suite_summary(
        name="quality",
        backend="mock",
        suite="golden",
        summary={
            "run_id": "x",
            "total_cases": 4,
            "passed": 0,
            "pass_rate": 0.0,
            "avg_latency_ms": 10.0,
        },
        failed_case_ids=["qa-001", "qa-002"],
        min_pass_rate=1.0,
        max_avg_latency_ms=5000,
    )
    assert r.ok is False
    assert any("pass_rate" in x for x in r.reasons)


def test_suite_fail_on_latency():
    r = evaluate_suite_summary(
        name="quality",
        backend="golden",
        suite="golden",
        summary={
            "run_id": "x",
            "total_cases": 1,
            "passed": 1,
            "pass_rate": 1.0,
            "avg_latency_ms": 9000.0,
        },
        failed_case_ids=[],
        min_pass_rate=1.0,
        max_avg_latency_ms=100.0,
    )
    assert r.ok is False
    assert any("latency" in x for x in r.reasons)


def test_suite_fail_empty_cases():
    r = evaluate_suite_summary(
        name="quality",
        backend="golden",
        suite="golden",
        summary={"total_cases": 0, "passed": 0, "pass_rate": 0.0, "avg_latency_ms": 0},
        failed_case_ids=[],
        min_pass_rate=1.0,
        max_avg_latency_ms=None,
    )
    assert r.ok is False
    assert any("no cases" in x for x in r.reasons)


def test_baseline_drop():
    reasons = evaluate_baseline_drop(
        current_pass_rate=0.5,
        baseline_pass_rate=0.9,
        max_drop=0.1,
    )
    assert reasons
    assert evaluate_baseline_drop(
        current_pass_rate=0.85,
        baseline_pass_rate=0.9,
        max_drop=0.1,
    ) == []


def test_decide_gate_green():
    r = evaluate_suite_summary(
        name="q",
        backend="golden",
        suite="golden",
        summary={
            "run_id": "1",
            "total_cases": 2,
            "passed": 2,
            "pass_rate": 1.0,
            "avg_latency_ms": 5,
        },
        failed_case_ids=[],
        min_pass_rate=1.0,
        max_avg_latency_ms=100,
    )
    d = decide_gate(
        profile="pr",
        policy_name="test",
        suite_results=[r],
        baseline_enabled=False,
    )
    assert d.ok is True
    assert d.exit_code == 0


def test_decide_gate_red():
    r = evaluate_suite_summary(
        name="q",
        backend="mock",
        suite="golden",
        summary={
            "run_id": "1",
            "total_cases": 2,
            "passed": 0,
            "pass_rate": 0.0,
            "avg_latency_ms": 5,
        },
        failed_case_ids=["qa-001"],
        min_pass_rate=1.0,
        max_avg_latency_ms=100,
    )
    d = decide_gate(profile="pr", policy_name="test", suite_results=[r])
    assert d.ok is False
    assert d.exit_code == 1


def test_decide_gate_no_suites():
    d = decide_gate(profile="pr", policy_name="test", suite_results=[])
    assert d.exit_code == 2
