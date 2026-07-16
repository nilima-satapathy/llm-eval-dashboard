"""
M3 DeepEval metric: Answer Relevancy (LLM-as-judge).

Opt-in only: set RUN_DEEPEVAL=1 and provide a judge API key.
Default offline CI stays green without network or free-tier spend.
"""

from __future__ import annotations

import os

import pytest

from src.dataset import get_case

pytest.importorskip("deepeval")

from deepeval.metrics import AnswerRelevancyMetric  # noqa: E402
from deepeval.test_case import LLMTestCase  # noqa: E402

RUN = os.getenv("RUN_DEEPEVAL", "").strip() in ("1", "true", "yes")
HAS_JUDGE_KEY = bool(
    (os.getenv("OPENAI_API_KEY") or os.getenv("XAI_API_KEY") or "").strip()
)

pytestmark = [
    pytest.mark.deepeval,
    pytest.mark.skipif(
        not RUN or not HAS_JUDGE_KEY,
        reason="DeepEval opt-in: set RUN_DEEPEVAL=1 and OPENAI_API_KEY (judge)",
    ),
]


@pytest.mark.parametrize("case_id", ["qa-001", "qa-002"])
def test_answer_relevancy_deepeval(case_id: str, target):
    case = get_case(case_id)
    result = target.complete(case["question"])

    test_case = LLMTestCase(
        input=case["question"],
        actual_output=result.answer,
    )
    metric = AnswerRelevancyMetric(threshold=0.5)
    metric.measure(test_case)
    assert metric.success, (
        f"{case_id}: AnswerRelevancy failed "
        f"score={getattr(metric, 'score', None)} reason={getattr(metric, 'reason', None)}"
    )
