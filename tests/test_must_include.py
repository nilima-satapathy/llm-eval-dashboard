"""
Metric 1: must_include coverage against the target answer.

Offline when TARGET_BACKEND=golden (default in conftest).
M4 runs the full golden set (40+ cases).
"""

from __future__ import annotations

import pytest

from src.dataset import get_case, load_cases
from src.metrics_basic import must_include_score, must_not_include_violations

THRESHOLD = 0.7


def _all_case_ids() -> list[str]:
    return [c["id"] for c in load_cases()]


@pytest.mark.parametrize("case_id", _all_case_ids())
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


def test_dataset_size_m4():
    assert len(load_cases()) >= 40
