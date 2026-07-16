"""Baseline helpers for quality-gate regression checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "gate" / "baseline.json"


def load_baseline(path: Path | None = None) -> dict[str, Any] | None:
    p = path or DEFAULT_BASELINE
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return data


def save_baseline(
    *,
    overall_pass_rate: float,
    profile: str,
    run_ids: list[str],
    path: Path | None = None,
) -> Path:
    p = path or DEFAULT_BASELINE
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "overall_pass_rate": overall_pass_rate,
        "profile": profile,
        "run_ids": run_ids,
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


def baseline_pass_rate(path: Path | None = None) -> float | None:
    data = load_baseline(path)
    if not data:
        return None
    val = data.get("overall_pass_rate")
    return float(val) if val is not None else None
