"""Load golden dataset cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "golden_dataset" / "qa_pairs.json"


def load_golden(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    return load_golden(path)["cases"]


def get_case(case_id: str, path: Path | None = None) -> dict[str, Any]:
    for case in load_cases(path):
        if case["id"] == case_id:
            return case
    raise KeyError(f"Unknown case id: {case_id}")
