"""Pytest fixtures for LLM eval suite."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dataset import load_cases  # noqa: E402
from src.target_app import get_target  # noqa: E402


@pytest.fixture(scope="session")
def golden_cases():
    return load_cases()


@pytest.fixture(scope="session")
def seed_case_ids():
    """Legacy small subset; M4 tests parametrize the full set."""
    return ["qa-001", "qa-002", "qa-004", "qa-007"]


@pytest.fixture(scope="session")
def all_case_ids(golden_cases):
    return [c["id"] for c in golden_cases]


@pytest.fixture(scope="session")
def target():
    """
    Default SUT for offline tests: golden reference answers.

    Override with TARGET_BACKEND=openai for real model eval.
    """
    backend = os.getenv("TARGET_BACKEND", "golden")
    return get_target(backend)
