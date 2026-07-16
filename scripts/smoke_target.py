#!/usr/bin/env python3
"""
M2 smoke: call the target app with one golden-set question (or a custom prompt).

Usage (from repo root):
  python scripts/smoke_target.py
  python scripts/smoke_target.py --id qa-002
  python scripts/smoke_target.py --prompt "What is regression testing?"
  set TARGET_BACKEND=openai && python scripts/smoke_target.py --id qa-001
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.target_app import ask  # noqa: E402


def load_case(case_id: str) -> dict:
    path = ROOT / "golden_dataset" / "qa_pairs.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for case in data["cases"]:
        if case["id"] == case_id:
            return case
    raise SystemExit(f"Case not found: {case_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test target_app.complete()")
    parser.add_argument("--id", default="qa-002", help="Golden case id (default qa-002)")
    parser.add_argument("--prompt", default=None, help="Override prompt text")
    parser.add_argument(
        "--backend",
        default=None,
        help="mock|openai (default: TARGET_BACKEND env or mock)",
    )
    args = parser.parse_args()

    if args.prompt:
        prompt = args.prompt
        case_id = None
    else:
        case = load_case(args.id)
        prompt = case["question"]
        case_id = case["id"]

    print(f"case_id={case_id or 'custom'}")
    print(f"prompt={prompt!r}")
    print("---")
    result = ask(prompt, backend=args.backend)
    print(f"backend={result.backend} model={result.model}")
    print(f"latency_ms={result.latency_ms}")
    if result.total_tokens is not None:
        print(
            f"tokens prompt={result.prompt_tokens} "
            f"completion={result.completion_tokens} total={result.total_tokens}"
        )
    print("--- answer ---")
    print(result.answer)


if __name__ == "__main__":
    main()
