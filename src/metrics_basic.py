"""
Offline metrics (no LLM judge).

Metric 1 (M3): must_include coverage
Metric 2 (M4): reference token overlap (Jaccard)

DeepEval LLM-as-judge metrics live in tests that need OPENAI_API_KEY.
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?", re.I)
# Stopwords ignored when doing soft phrase matching (token subset)
_SOFT_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "is",
        "are",
        "be",
        "as",
        "by",
        "with",
    }
)


def _normalize(text: str) -> str:
    """Lowercase, unify hyphens/slashes, collapse whitespace for matching."""
    t = text.lower()
    t = t.replace("—", " ").replace("–", " ").replace("-", " ").replace("/", " ")
    t = re.sub(r"[^a-z0-9'\s]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(_normalize(text))}


def _phrase_hit(answer_norm: str, answer_tokens: set[str], phrase: str) -> bool:
    """
    Phrase counts as present if:
    1) normalized substring match, or
    2) soft match: all content tokens of the phrase appear in the answer.
    """
    p_norm = _normalize(phrase)
    if not p_norm:
        return True
    if p_norm in answer_norm:
        return True
    p_tokens = [t for t in _tokens(phrase) if t not in _SOFT_STOP and len(t) > 1]
    if not p_tokens:
        return p_norm in answer_norm
    # Soft: every content token must appear (order-free)
    return all(t in answer_tokens for t in p_tokens)


def must_include_score(answer: str, must_include: list[str]) -> float:
    """
    Fraction of required concepts found in the answer (case-insensitive).

    Uses substring match plus soft token match so live models that paraphrase
    slightly still get credit (e.g. "non-deterministic" vs "non deterministic").

    Returns 0.0–1.0. Empty must_include → 1.0.
    """
    if not must_include:
        return 1.0
    answer_norm = _normalize(answer)
    answer_tokens = _tokens(answer)
    hits = sum(
        1 for phrase in must_include if _phrase_hit(answer_norm, answer_tokens, phrase)
    )
    return hits / len(must_include)


def must_not_include_violations(answer: str, must_not_include: list[str]) -> list[str]:
    """Return list of forbidden phrases that appear in the answer (substring only)."""
    answer_norm = _normalize(answer)
    out: list[str] = []
    for p in must_not_include:
        p_norm = _normalize(p)
        if p_norm and p_norm in answer_norm:
            out.append(p)
    return out


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
