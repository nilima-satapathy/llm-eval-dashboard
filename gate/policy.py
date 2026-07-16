"""Load and validate quality-gate policy YAML."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "gate" / "policy.yaml"


@dataclass
class SuitePolicy:
    name: str
    enabled: bool
    backend: str
    suite: str  # golden | red_team | all
    case_ids: list[str] | None
    min_pass_rate: float
    max_avg_latency_ms: float | None


@dataclass
class BaselinePolicy:
    enabled: bool
    max_pass_rate_drop: float


@dataclass
class GatePolicy:
    version: int
    name: str
    profile: str
    suites: list[SuitePolicy]
    baseline: BaselinePolicy
    raw: dict[str, Any] = field(default_factory=dict)


def load_policy(
    path: Path | None = None,
    *,
    profile: str | None = None,
) -> GatePolicy:
    """
    Load policy.yaml and select a profile (pr | full | live).

    Profile can be overridden by env GATE_PROFILE.
    """
    p = path or DEFAULT_POLICY
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid policy file: {p}")

    profiles = data.get("profiles") or {}
    if not profiles:
        raise ValueError("policy must define profiles")

    chosen = (profile or os.getenv("GATE_PROFILE") or "pr").strip().lower()
    if chosen not in profiles:
        raise ValueError(
            f"Unknown profile={chosen!r}. Available: {sorted(profiles)}"
        )

    block = profiles[chosen]
    suites_raw = block.get("suites") or {}
    suites: list[SuitePolicy] = []
    for name, cfg in suites_raw.items():
        if not isinstance(cfg, dict):
            raise ValueError(f"suite {name} must be a mapping")
        case_ids = cfg.get("case_ids")
        if case_ids is not None and not isinstance(case_ids, list):
            raise ValueError(f"suite {name}: case_ids must be a list or null")
        max_lat = cfg.get("max_avg_latency_ms")
        suites.append(
            SuitePolicy(
                name=name,
                enabled=bool(cfg.get("enabled", True)),
                backend=str(cfg.get("backend") or "golden").strip().lower(),
                suite=str(cfg.get("suite") or "golden").strip().lower(),
                case_ids=[str(x) for x in case_ids] if case_ids else None,
                min_pass_rate=float(cfg.get("min_pass_rate", 1.0)),
                max_avg_latency_ms=float(max_lat) if max_lat is not None else None,
            )
        )

    base_raw = block.get("baseline") or {}
    baseline = BaselinePolicy(
        enabled=bool(base_raw.get("enabled", False)),
        max_pass_rate_drop=float(base_raw.get("max_pass_rate_drop", 0.10)),
    )

    return GatePolicy(
        version=int(data.get("version") or 1),
        name=str(data.get("name") or "quality-gate"),
        profile=chosen,
        suites=suites,
        baseline=baseline,
        raw=data,
    )
