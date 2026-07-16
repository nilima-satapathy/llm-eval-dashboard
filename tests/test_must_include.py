"""
M3 offline gate: must_include coverage against the target answer.

Runs without API keys when TARGET_BACKEND=golden (default in conftest).
"""

from __future__ import annotations

import pytest

from src.dataset import get_case
from src.metrics_basic import must_include_score, must_not_include_violations

# Pass if at least 70% of required concepts appear in the answer
THRESHOLD = 0.7


@pytest.mark.parametrize("case_id", ["qa-001", "qa-002", "qa-004", "qa-007"])
def test_must_include_coverage(case_id: str, target):
    case = get_case(case_id)
    result = target.complete(case["question"])
    score = must_include_score(result.answer, case["must_include"])
    assert score >= THRESHOLD, (
        f"{case_id}: must_include score {score:.2f} < {THRESHOLD}. "
        f"answer={result.answer!r} required={case['must_include']}"
    )
    violations = must_not_include_violations(
        result.answer, case.get("must_not_include") or []
    )
    assert not violations, f"{case_id}: forbidden phrases present: {violations}"


def test_latency_is_recorded(target):
    result = target.complete("What is a flaky test, and why is it harmful in CI?")
    assert result.latency_ms >= 0
    assert result.answer
    assert result.backend in ("golden", "mock", "openai")
