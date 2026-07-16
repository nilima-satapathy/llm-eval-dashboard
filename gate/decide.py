"""Pure gate decision logic (unit-test friendly, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SuiteGateResult:
    name: str
    backend: str
    suite: str
    total_cases: int
    passed: int
    pass_rate: float
    min_pass_rate: float
    avg_latency_ms: float
    max_avg_latency_ms: float | None
    failed_case_ids: list[str]
    ok: bool
    reasons: list[str] = field(default_factory=list)
    run_id: str = ""


@dataclass
class GateDecision:
    ok: bool
    profile: str
    policy_name: str
    suite_results: list[SuiteGateResult]
    baseline_reasons: list[str] = field(default_factory=list)
    overall_pass_rate: float | None = None
    exit_code: int = 0  # 0 green, 1 red policy, 2 config/runtime


def evaluate_suite_summary(
    *,
    name: str,
    backend: str,
    suite: str,
    summary: dict[str, Any],
    failed_case_ids: list[str],
    min_pass_rate: float,
    max_avg_latency_ms: float | None,
) -> SuiteGateResult:
    """Score one suite run summary against absolute thresholds."""
    total = int(summary.get("total_cases") or 0)
    passed = int(summary.get("passed") or 0)
    pass_rate = float(summary.get("pass_rate") or 0.0)
    avg_lat = float(summary.get("avg_latency_ms") or 0.0)
    reasons: list[str] = []

    if total <= 0:
        reasons.append("no cases executed")
    if pass_rate + 1e-9 < min_pass_rate:
        reasons.append(
            f"pass_rate {pass_rate:.1%} < min_pass_rate {min_pass_rate:.1%}"
        )
    if max_avg_latency_ms is not None and avg_lat > max_avg_latency_ms:
        reasons.append(
            f"avg_latency_ms {avg_lat:.1f} > max {max_avg_latency_ms:.1f}"
        )

    ok = not reasons
    return SuiteGateResult(
        name=name,
        backend=backend,
        suite=suite,
        total_cases=total,
        passed=passed,
        pass_rate=pass_rate,
        min_pass_rate=min_pass_rate,
        avg_latency_ms=avg_lat,
        max_avg_latency_ms=max_avg_latency_ms,
        failed_case_ids=list(failed_case_ids),
        ok=ok,
        reasons=reasons,
        run_id=str(summary.get("run_id") or ""),
    )


def evaluate_baseline_drop(
    *,
    current_pass_rate: float,
    baseline_pass_rate: float | None,
    max_drop: float,
) -> list[str]:
    """Return failure reasons if pass rate dropped more than allowed vs baseline."""
    if baseline_pass_rate is None:
        return []
    drop = float(baseline_pass_rate) - float(current_pass_rate)
    if drop > max_drop + 1e-9:
        return [
            f"pass_rate drop {drop:.1%} exceeds max_pass_rate_drop {max_drop:.1%} "
            f"(baseline {baseline_pass_rate:.1%} → current {current_pass_rate:.1%})"
        ]
    return []


def decide_gate(
    *,
    profile: str,
    policy_name: str,
    suite_results: list[SuiteGateResult],
    baseline_pass_rate: float | None = None,
    baseline_enabled: bool = False,
    max_pass_rate_drop: float = 0.10,
) -> GateDecision:
    """Aggregate suite results (+ optional baseline) into a gate decision."""
    if not suite_results:
        return GateDecision(
            ok=False,
            profile=profile,
            policy_name=policy_name,
            suite_results=[],
            baseline_reasons=["no suites executed"],
            exit_code=2,
        )

    suites_ok = all(r.ok for r in suite_results)
    overall = sum(r.pass_rate for r in suite_results) / len(suite_results)

    baseline_reasons: list[str] = []
    if baseline_enabled:
        baseline_reasons = evaluate_baseline_drop(
            current_pass_rate=overall,
            baseline_pass_rate=baseline_pass_rate,
            max_drop=max_pass_rate_drop,
        )

    ok = suites_ok and not baseline_reasons
    return GateDecision(
        ok=ok,
        profile=profile,
        policy_name=policy_name,
        suite_results=suite_results,
        baseline_reasons=baseline_reasons,
        overall_pass_rate=round(overall, 4),
        exit_code=0 if ok else 1,
    )
