"""Unit tests for offline metrics (no SUT / no network)."""

from __future__ import annotations

from src.metrics_basic import (
    must_include_score,
    must_not_include_violations,
    reference_overlap_score,
)
from src.metrics_store import estimate_cost_usd, p95


def test_must_include_all_hit():
    assert must_include_score("Flaky tests fail intermittently in CI", ["flaky", "CI"]) == 1.0


def test_must_include_partial():
    assert must_include_score("only flaky mentioned", ["flaky", "regression"]) == 0.5


def test_must_include_empty_list_is_pass():
    assert must_include_score("anything", []) == 1.0


def test_must_include_case_insensitive():
    assert must_include_score("REGRESSION testing", ["regression"]) == 1.0


def test_must_not_include_detects_forbidden():
    v = must_not_include_violations("I am not a doctor", ["not a doctor"])
    assert v == ["not a doctor"]


def test_must_not_include_clean():
    assert must_not_include_violations("solid answer", ["hallucination"]) == []


def test_reference_overlap_identical():
    text = "Boundary value analysis tests edges of input ranges."
    assert reference_overlap_score(text, text) == 1.0


def test_reference_overlap_empty_both():
    assert reference_overlap_score("", "") == 1.0


def test_reference_overlap_one_empty():
    assert reference_overlap_score("hello", "") == 0.0


def test_reference_overlap_disjoint():
    score = reference_overlap_score("alpha beta", "gamma delta")
    assert score == 0.0


def test_p95_empty():
    assert p95([]) == 0.0


def test_p95_known_order():
    # 20 values 1..20 → p95 index near top
    vals = [float(i) for i in range(1, 21)]
    assert p95(vals) >= 19.0


def test_estimate_cost_none_tokens():
    assert estimate_cost_usd(None) is None


def test_estimate_cost_math():
    # 1M tokens at 0.15 → 0.15
    assert estimate_cost_usd(1_000_000, usd_per_1m_tokens=0.15) == 0.15
