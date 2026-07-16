"""
M4 second metric: reference token overlap (Jaccard).

Offline — no API key. With TARGET_BACKEND=golden, scores should be ~1.0.
"""

from __future__ import annotations

import pytest

from src.dataset import get_case, load_cases
from src.metrics_basic import reference_overlap_score

# Golden SUT returns exact reference → high overlap; allow slight float noise
THRESHOLD = 0.85


def _all_case_ids() -> list[str]:
    return [c["id"] for c in load_cases()]


@pytest.mark.parametrize("case_id", _all_case_ids())
def test_reference_overlap_all_cases(case_id: str, target):
    case = get_case(case_id)
    result = target.complete(case["question"])
    score = reference_overlap_score(result.answer, case["reference_answer"])
    assert score >= THRESHOLD, (
        f"{case_id}: reference_overlap {score:.3f} < {THRESHOLD}. "
        f"backend={result.backend} answer_len={len(result.answer)}"
    )


def test_dataset_has_at_least_40_cases():
    cases = load_cases()
    assert len(cases) >= 40, f"M4 requires >=40 cases, found {len(cases)}"
