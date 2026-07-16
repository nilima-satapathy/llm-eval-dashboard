"""
Offline metrics (no LLM judge).

Metric 1 (M3): must_include coverage
Metric 2 (M4): reference token overlap (Jaccard)

DeepEval LLM-as-judge metrics live in tests that need OPENAI_API_KEY.
"""

from __future__ import annotations

import re


_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?", re.I)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text)}


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


def reference_overlap_score(answer: str, reference_answer: str) -> float:
    """
    Jaccard overlap of word tokens between answer and reference.

    Returns 0.0–1.0. Useful offline second metric; golden SUT should score ~1.0.
    """
    a = _tokens(answer)
    b = _tokens(reference_answer)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
