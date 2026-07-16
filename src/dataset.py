"""Load golden and red-team dataset cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "golden_dataset" / "qa_pairs.json"
RED_TEAM_PATH = ROOT / "golden_dataset" / "red_team_cases.json"

SuiteName = Literal["golden", "red_team", "all"]


def load_golden(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def load_red_team(path: Path | None = None) -> dict[str, Any]:
    p = path or RED_TEAM_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def load_cases(
    path: Path | None = None,
    *,
    suite: SuiteName = "golden",
) -> list[dict[str, Any]]:
    """
    Load cases for a suite.

    suite:
      golden   — quality cases (qa-*)
      red_team — adversarial cases (rt-*)
      all      — golden then red_team
    """
    if suite == "golden":
        cases = load_golden(path)["cases"]
    elif suite == "red_team":
        cases = load_red_team()["cases"]
    elif suite == "all":
        cases = list(load_golden(path)["cases"]) + list(load_red_team()["cases"])
    else:
        raise ValueError(f"Unknown suite={suite!r}. Use golden|red_team|all.")

    # Ensure eval_mode is set for scoring
    for c in cases:
        if "eval_mode" not in c:
            cid = str(c.get("id", ""))
            c["eval_mode"] = "red_team" if cid.startswith("rt-") else "quality"
    return cases


def get_case(case_id: str, path: Path | None = None) -> dict[str, Any]:
    # Search both suites
    for suite in ("golden", "red_team"):
        for case in load_cases(path, suite=suite):  # type: ignore[arg-type]
            if case["id"] == case_id:
                return case
    raise KeyError(f"Unknown case id: {case_id}")


def is_red_team_case(case: dict[str, Any]) -> bool:
    if case.get("eval_mode") == "red_team":
        return True
    return str(case.get("id", "")).startswith("rt-")
