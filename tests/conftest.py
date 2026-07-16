"""Pytest fixtures for LLM eval suite.

Offline tests always use the golden SUT so a developer's .env
(TARGET_BACKEND=openai / Groq) cannot pollute CI or local pytest.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Isolate offline suite from project .env live-backend settings
os.environ["TARGET_BACKEND"] = "golden"

from src.dataset import load_cases  # noqa: E402
from src.target_app import get_target  # noqa: E402


@pytest.fixture(scope="session")
def golden_cases():
    return load_cases()


@pytest.fixture(scope="session")
def seed_case_ids():
    """Quick-run subset used by the dashboard."""
    return ["qa-001", "qa-002", "qa-004", "qa-007"]


@pytest.fixture(scope="session")
def all_case_ids(golden_cases):
    return [c["id"] for c in golden_cases]


@pytest.fixture(scope="session")
def target():
    """
    Offline SUT: golden reference answers.

    Live API eval is not part of the default pytest target fixture.
    Use scripts/run_eval.py --backend openai for real model runs.
    """
    return get_target("golden")
