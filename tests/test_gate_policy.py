"""Tests for gate policy loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from gate.policy import load_policy

ROOT = Path(__file__).resolve().parents[1]


def test_load_default_pr_profile():
    p = load_policy(ROOT / "gate" / "policy.yaml", profile="pr")
    assert p.profile == "pr"
    assert p.name
    names = {s.name for s in p.suites}
    assert "quality" in names
    assert "red_team" in names
    quality = next(s for s in p.suites if s.name == "quality")
    assert quality.enabled
    assert quality.backend == "golden"
    assert quality.case_ids is not None
    assert len(quality.case_ids) == 4
    assert quality.min_pass_rate == 1.0


def test_load_full_profile():
    p = load_policy(profile="full")
    assert p.profile == "full"
    assert p.baseline.enabled is True
    quality = next(s for s in p.suites if s.name == "quality")
    assert quality.case_ids is None  # full suite


def test_unknown_profile_raises():
    with pytest.raises(ValueError, match="Unknown profile"):
        load_policy(profile="nope")
