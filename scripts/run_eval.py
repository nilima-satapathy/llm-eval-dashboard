#!/usr/bin/env python3
"""
M5/M7 — Run full (or subset) evaluation and persist results.

Usage (repo root):
  python scripts/run_eval.py
  python scripts/run_eval.py --backend golden
  python scripts/run_eval.py --suite red_team
  python scripts/run_eval.py --ids qa-001,qa-002
  python scripts/run_eval.py --no-csv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.runners import run_evaluation  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM eval suite and store results")
    parser.add_argument(
        "--backend",
        default=None,
        help="mock|golden|openai (default: TARGET_BACKEND or golden)",
    )
    parser.add_argument(
        "--suite",
        default="golden",
        choices=["golden", "red_team", "all"],
        help="golden quality set | red_team adversarial | all",
    )
    parser.add_argument(
        "--ids",
        default=None,
        help="Comma-separated case ids (default: all in suite)",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional note stored on the run",
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Skip CSV export under reports/",
    )
    args = parser.parse_args()

    case_ids = None
    if args.ids:
        case_ids = [x.strip() for x in args.ids.split(",") if x.strip()]

    backend = args.backend or "golden"
    out = run_evaluation(
        backend=backend,
        case_ids=case_ids,
        suite=args.suite,
        notes=args.notes,
        export_csv=not args.no_csv,
    )
    s = out["summary"]
    print("=== Eval run complete ===")
    print(f"run_id={s['run_id']}")
    print(f"backend={s['backend']} model={s['model']}")
    print(
        f"passed={s['passed']}/{s['total_cases']} "
        f"pass_rate={s['pass_rate']:.1%} "
        f"avg_latency_ms={s['avg_latency_ms']} "
        f"p95_latency_ms={s['p95_latency_ms']}"
    )
    if s.get("total_tokens") is not None:
        print(f"total_tokens={s['total_tokens']} est_cost_usd={s['estimated_cost_usd']}")
    print(f"db={out['db_path']}")
    if out.get("csv_path"):
        print(f"csv={out['csv_path']}")
    if out.get("comparison"):
        c = out["comparison"]
        print(
            f"vs previous: pass_rate_delta={c['pass_rate_delta']:+.1%} "
            f"(was {c['older_pass_rate']:.1%})"
        )
    if out.get("failed_case_ids"):
        print("failed:", ", ".join(out["failed_case_ids"]))
    print(json.dumps(out["summary"], indent=2))


if __name__ == "__main__":
    main()
