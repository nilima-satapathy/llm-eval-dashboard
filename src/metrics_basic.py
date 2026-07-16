"""
Offline metrics (no LLM judge). Used so M3 pytest is green without API keys.

DeepEval LLM-as-judge metrics live in tests that need OPENAI_API_KEY.
"""

from __future__ import annotations


def must_include_score(answer: str, must_include: list[str]) -> float:
    """
    Fraction of required concepts found in the answer (case-insensitive).

    Returns 0.0–1.0. Empty must_include → 1.0.
    """
    if not must_include:
        return 1.0
    text = answer.lower()
    hits = sum(1 for phrase in must_include if phrase.lower() in text)
    return hits / len(must_include)


def must_not_include_violations(answer: str, must_not_include: list[str]) -> list[str]:
    """Return list of forbidden phrases that appear in the answer."""
    text = answer.lower()
    return [p for p in must_not_include if p.lower() in text]
