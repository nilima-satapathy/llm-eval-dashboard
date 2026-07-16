"""
M3 DeepEval metric: Answer Relevancy (LLM-as-judge).

Requires OPENAI_API_KEY (or XAI_API_KEY) for the *judge* model.
SUT can still be golden/mock/openai via TARGET_BACKEND.

Skip cleanly when no key is configured so offline CI stays green.
"""

from __future__ import annotations

import os

import pytest

from src.dataset import get_case

pytest.importorskip("deepeval")

from deepeval.metrics import AnswerRelevancyMetric  # noqa: E402
from deepeval.test_case import LLMTestCase  # noqa: E402

HAS_JUDGE_KEY = bool(os.getenv("OPENAI_API_KEY") or os.getenv("XAI_API_KEY"))

pytestmark = pytest.mark.skipif(
    not HAS_JUDGE_KEY,
    reason="DeepEval AnswerRelevancy needs OPENAI_API_KEY or XAI_API_KEY for the judge",
)


@pytest.mark.deepeval
@pytest.mark.parametrize("case_id", ["qa-001", "qa-002"])
def test_answer_relevancy_deepeval(case_id: str, target):
    case = get_case(case_id)
    result = target.complete(case["question"])

    test_case = LLMTestCase(
        input=case["question"],
        actual_output=result.answer,
    )
    # Slightly lenient threshold for M3 wiring; tighten in M4+
    metric = AnswerRelevancyMetric(threshold=0.5)
    metric.measure(test_case)
    assert metric.success, (
        f"{case_id}: AnswerRelevancy failed "
        f"score={getattr(metric, 'score', None)} reason={getattr(metric, 'reason', None)}"
    )
