"""Write human + machine readable quality-gate reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gate.decide import GateDecision

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_gate_reports(
    decision: GateDecision,
    *,
    reports_dir: Path | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Write gate_<stamp>.md and .json; return paths."""
    out_dir = Path(reports_dir or REPORTS)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _utc_stamp()
    base = out_dir / f"gate_{stamp}"

    status = "PASSED" if decision.ok else "FAILED"
    overall_line = (
        f"- Overall pass rate (mean of suites): {decision.overall_pass_rate:.1%}"
        if decision.overall_pass_rate is not None
        else "- Overall pass rate: n/a"
    )
    lines = [
        f"# LLM Quality Gate — **{status}**",
        "",
        f"- Policy: `{decision.policy_name}`",
        f"- Profile: `{decision.profile}`",
        overall_line,
        f"- Exit code: `{decision.exit_code}`",
        "",
        "| Suite | Backend | Eval suite | Passed | Total | Pass rate | Threshold | Avg latency | Result |",
        "|-------|---------|------------|--------|-------|-----------|-----------|-------------|--------|",
    ]
    for r in decision.suite_results:
        thr = f"{r.min_pass_rate:.0%}"
        lat_lim = (
            f"{r.max_avg_latency_ms:.0f}"
            if r.max_avg_latency_ms is not None
            else "—"
        )
        lines.append(
            f"| {r.name} | {r.backend} | {r.suite} | {r.passed} | {r.total_cases} | "
            f"{r.pass_rate:.1%} | {thr} | {r.avg_latency_ms:.1f} ms (max {lat_lim}) | "
            f"{'PASS' if r.ok else 'FAIL'} |"
        )

    if decision.baseline_reasons:
        lines.extend(["", "## Baseline", ""])
        for reason in decision.baseline_reasons:
            lines.append(f"- {reason}")

    fail_lines: list[str] = []
    for r in decision.suite_results:
        if r.reasons:
            for reason in r.reasons:
                fail_lines.append(f"- **{r.name}**: {reason}")
        if r.failed_case_ids:
            fail_lines.append(
                f"- **{r.name}** failed cases: {', '.join(r.failed_case_ids)}"
            )
    if fail_lines:
        lines.extend(["", "## Failures", ""] + fail_lines)

    lines.extend(
        [
            "",
            "## How to extend",
            "",
            "1. Add cases to `golden_dataset/qa_pairs.json` or `red_team_cases.json`.",
            "2. Adjust thresholds in `gate/policy.yaml` (do not hard-code in CI).",
            "3. Re-run: `python scripts/run_gate.py`.",
            "",
        ]
    )

    md_path = base.with_suffix(".md")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload: dict[str, Any] = {
        "ok": decision.ok,
        "exit_code": decision.exit_code,
        "profile": decision.profile,
        "policy_name": decision.policy_name,
        "overall_pass_rate": decision.overall_pass_rate,
        "baseline_reasons": decision.baseline_reasons,
        "suites": [
            {
                "name": r.name,
                "backend": r.backend,
                "suite": r.suite,
                "total_cases": r.total_cases,
                "passed": r.passed,
                "pass_rate": r.pass_rate,
                "min_pass_rate": r.min_pass_rate,
                "avg_latency_ms": r.avg_latency_ms,
                "max_avg_latency_ms": r.max_avg_latency_ms,
                "failed_case_ids": r.failed_case_ids,
                "ok": r.ok,
                "reasons": r.reasons,
                "run_id": r.run_id,
            }
            for r in decision.suite_results
        ],
    }
    if extra:
        payload["extra"] = extra

    json_path = base.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    (out_dir / "gate_latest.md").write_text(
        md_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (out_dir / "gate_latest.json").write_text(
        json_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    return {"md": str(md_path), "json": str(json_path)}
