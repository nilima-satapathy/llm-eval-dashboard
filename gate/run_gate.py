"""
Orchestrate quality-gate runs: policy → eval suites → decide → report → exit code.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gate.baseline import baseline_pass_rate, save_baseline  # noqa: E402
from gate.decide import decide_gate, evaluate_suite_summary  # noqa: E402
from gate.policy import DEFAULT_POLICY, load_policy  # noqa: E402
from gate.report import write_gate_reports  # noqa: E402
from src.metrics_store import MetricsStore  # noqa: E402
from src.runners import run_evaluation  # noqa: E402


def run_quality_gate(
    *,
    profile: str = "pr",
    policy_path: Path | None = None,
    soft_fail: bool = False,
    export_csv: bool = False,
    store: MetricsStore | None = None,
    backend_override: str | None = None,
) -> tuple[int, dict[str, Any]]:
    """
    Run the gate. Returns (exit_code, payload).

    soft_fail: always return exit 0 after writing report (demo mode).
    """
    try:
        policy = load_policy(policy_path, profile=profile)
    except Exception as exc:  # noqa: BLE001
        return 2, {"error": f"policy load failed: {exc}"}

    metrics_store = store or MetricsStore()
    suite_results = []
    run_ids: list[str] = []

    enabled = [s for s in policy.suites if s.enabled]
    if not enabled:
        decision = decide_gate(
            profile=policy.profile,
            policy_name=policy.name,
            suite_results=[],
        )
        paths = write_gate_reports(decision, extra={"error": "no enabled suites"})
        return 2, {"decision": decision, "reports": paths}

    for sp in enabled:
        backend = backend_override or sp.backend
        out = run_evaluation(
            backend=backend,
            suite=sp.suite,  # type: ignore[arg-type]
            case_ids=sp.case_ids,
            store=metrics_store,
            notes=f"quality-gate; profile={policy.profile}; suite_name={sp.name}",
            export_csv=export_csv,
        )
        summary = out["summary"]
        run_ids.append(summary.get("run_id") or "")
        suite_results.append(
            evaluate_suite_summary(
                name=sp.name,
                backend=backend,
                suite=sp.suite,
                summary=summary,
                failed_case_ids=out.get("failed_case_ids") or [],
                min_pass_rate=sp.min_pass_rate,
                max_avg_latency_ms=sp.max_avg_latency_ms,
            )
        )

    base_rate = baseline_pass_rate() if policy.baseline.enabled else None
    decision = decide_gate(
        profile=policy.profile,
        policy_name=policy.name,
        suite_results=suite_results,
        baseline_pass_rate=base_rate,
        baseline_enabled=policy.baseline.enabled,
        max_pass_rate_drop=policy.baseline.max_pass_rate_drop,
    )

    paths = write_gate_reports(
        decision,
        extra={"run_ids": run_ids, "profile": policy.profile},
    )

    if decision.ok and decision.overall_pass_rate is not None:
        save_baseline(
            overall_pass_rate=decision.overall_pass_rate,
            profile=policy.profile,
            run_ids=[x for x in run_ids if x],
        )

    code = 0 if soft_fail else decision.exit_code
    return code, {
        "decision": decision,
        "reports": paths,
        "run_ids": run_ids,
        "ok": decision.ok,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="LLM Quality Gate — fail CI when eval policy is violated"
    )
    parser.add_argument(
        "--profile",
        default=None,
        choices=["pr", "full", "live"],
        help="Policy profile (default: pr or GATE_PROFILE)",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help=f"Path to policy.yaml (default: {DEFAULT_POLICY})",
    )
    parser.add_argument(
        "--backend",
        default=None,
        help="Override backend for all suites (e.g. mock to force fail)",
    )
    parser.add_argument(
        "--soft-fail",
        action="store_true",
        help="Write report but always exit 0 (demo mode)",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also export per-suite CSV reports",
    )
    args = parser.parse_args(argv)

    code, payload = run_quality_gate(
        profile=args.profile or "pr",
        policy_path=Path(args.policy) if args.policy else None,
        soft_fail=args.soft_fail,
        export_csv=args.csv,
        backend_override=args.backend,
    )

    if "error" in payload and "decision" not in payload:
        print(f"ERROR: {payload['error']}", file=sys.stderr)
        return code

    decision = payload["decision"]
    status = "PASSED" if decision.ok else "FAILED"
    print(f"=== LLM Quality Gate — {status} ===")
    print(f"profile={decision.profile} policy={decision.policy_name}")
    if decision.overall_pass_rate is not None:
        print(f"overall_pass_rate={decision.overall_pass_rate:.1%}")
    for r in decision.suite_results:
        mark = "OK" if r.ok else "FAIL"
        print(
            f"  [{mark}] {r.name}: {r.passed}/{r.total_cases} "
            f"({r.pass_rate:.0%}) backend={r.backend}"
        )
        for reason in r.reasons:
            print(f"       - {reason}")
    for reason in decision.baseline_reasons:
        print(f"  baseline: {reason}")
    reports = payload.get("reports") or {}
    if reports.get("md"):
        print(f"report={reports['md']}")
    print(f"exit_code={code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
