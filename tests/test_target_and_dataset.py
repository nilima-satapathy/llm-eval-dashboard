"""SUT backends, dataset integrity, and factory behaviour."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.dataset import get_case, load_cases, load_golden
from src.target_app import GoldenTarget, MockTarget, OpenAICompatibleTarget, get_target

ROOT = Path(__file__).resolve().parents[1]


def test_load_golden_structure():
    data = load_golden()
    assert data["domain"] == "software_testing_assistant"
    assert "cases" in data
    assert len(data["cases"]) >= 40


def test_case_ids_unique():
    ids = [c["id"] for c in load_cases()]
    assert len(ids) == len(set(ids))


def test_case_required_fields():
    required = {
        "id",
        "domain",
        "category",
        "difficulty",
        "question",
        "reference_answer",
        "must_include",
        "must_not_include",
        "tags",
        "source",
    }
    for case in load_cases():
        missing = required - set(case.keys())
        assert not missing, f"{case.get('id')}: missing {missing}"
        assert len(case["must_include"]) >= 2
        assert len(case["reference_answer"]) >= 40
        assert case["question"].strip()


def test_questions_unique():
    qs = [c["question"].strip() for c in load_cases()]
    assert len(qs) == len(set(qs)), "duplicate questions break GoldenTarget lookup"


def test_get_case_unknown_raises():
    with pytest.raises(KeyError):
        get_case("qa-999")


def test_mock_target_returns_placeholder():
    t = MockTarget()
    r = t.complete("What is smoke testing?")
    assert r.backend == "mock"
    assert r.answer
    assert "[mock]" in r.answer
    assert r.latency_ms >= 0


def test_golden_target_matches_reference():
    t = GoldenTarget()
    case = get_case("qa-001")
    r = t.complete(case["question"])
    assert r.backend == "golden"
    assert r.answer == case["reference_answer"]
    assert r.raw.get("matched") is True


def test_golden_target_miss_on_unknown_prompt():
    t = GoldenTarget()
    r = t.complete("this is not a golden question xyz")
    assert r.backend == "golden"
    assert r.raw.get("matched") is False
    assert "No matching" in r.answer


def test_get_target_factory_aliases():
    assert get_target("mock").name == "mock"
    assert get_target("golden").name == "golden"
    assert get_target("oracle").name == "golden"
    with pytest.raises(ValueError):
        get_target("not-a-backend")


def test_openai_target_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key required"):
        OpenAICompatibleTarget(api_key="", base_url="https://api.groq.com/openai/v1")


def test_openai_target_strips_key_whitespace(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    t = OpenAICompatibleTarget(
        api_key="  gsk_test_key  ",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant",
    )
    assert t.api_key == "gsk_test_key"


def test_schema_file_present():
    schema = json.loads((ROOT / "golden_dataset" / "schema.json").read_text(encoding="utf-8"))
    assert "cases" in schema["properties"]
