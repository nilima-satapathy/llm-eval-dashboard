"""
M5 — Run evaluation suite over golden cases and persist results.
"""

from __future__ import annotations

import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from src.dataset import load_cases
from src.metrics_basic import (
    must_include_score,
    must_not_include_violations,
    reference_overlap_score,
)
from src.metrics_store import (
    CaseResult,
    MetricsStore,
    RunSummary,
    estimate_cost_usd,
    new_run_id,
    p95,
)
from src.target_app import TargetApp, get_target

MUST_INCLUDE_THRESHOLD = float(os.getenv("MUST_INCLUDE_THRESHOLD") or "0.7")
OVERLAP_THRESHOLD = float(os.getenv("OVERLAP_THRESHOLD") or "0.85")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def evaluate_case(case: dict[str, Any], target: TargetApp) -> CaseResult:
    """Score one golden case against the target SUT."""
    question = case["question"]
    try:
        resp = target.complete(question)
        mi = must_include_score(resp.answer, case.get("must_include") or [])
        ov = reference_overlap_score(resp.answer, case.get("reference_answer") or "")
        violations = must_not_include_violations(
            resp.answer, case.get("must_not_include") or []
        )
        passed = (
            mi >= MUST_INCLUDE_THRESHOLD
            and ov >= OVERLAP_THRESHOLD
            and not violations
        )
        cost = estimate_cost_usd(resp.total_tokens)
        return CaseResult(
            case_id=case["id"],
            question=question,
            answer=resp.answer,
            passed=passed,
            must_include_score=round(mi, 4),
            reference_overlap_score=round(ov, 4),
            latency_ms=resp.latency_ms,
            prompt_tokens=resp.prompt_tokens,
            completion_tokens=resp.completion_tokens,
            total_tokens=resp.total_tokens,
            estimated_cost_usd=cost,
            model=resp.model,
            backend=resp.backend,
            error=None,
            details={"must_not_violations": violations},
        )
    except Exception as exc:  # noqa: BLE001 — record failure per case
        return CaseResult(
            case_id=case["id"],
            question=question,
            answer="",
            passed=False,
            must_include_score=0.0,
            reference_overlap_score=0.0,
            latency_ms=0.0,
            error=str(exc),
            details={},
        )


def run_evaluation(
    *,
    backend: str | None = None,
    case_ids: list[str] | None = None,
    store: MetricsStore | None = None,
    notes: str = "",
    export_csv: bool = True,
) -> dict[str, Any]:
    """
    Run metrics on golden cases, save to SQLite, optionally export CSV.

    Returns summary dict including run_id and paths.
    """
    target = get_target(backend)
    # Prefer explicit CLI/dashboard backend, then env, then resolved SUT name
    effective_backend = (backend or os.getenv("TARGET_BACKEND") or target.name).strip().lower()
    cases = load_cases()
    if case_ids:
        id_set = set(case_ids)
        cases = [c for c in cases if c["id"] in id_set]

    started = _utc_now()
    results: list[CaseResult] = []
    for case in cases:
        results.append(evaluate_case(case, target))
    finished = _utc_now()

    latencies = [r.latency_ms for r in results]
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    token_vals = [r.total_tokens for r in results if r.total_tokens is not None]
    total_tokens = sum(token_vals) if token_vals else None
    cost_vals = [
        r.estimated_cost_usd for r in results if r.estimated_cost_usd is not None
    ]
    total_cost = round(sum(cost_vals), 6) if cost_vals else estimate_cost_usd(total_tokens)

    models = {r.model for r in results if r.model}
    model_label = ",".join(sorted(models)) if models else target.name

    summary = RunSummary(
        run_id=new_run_id(),
        started_at=started,
        finished_at=finished,
        backend=target.name if target.name else effective_backend,
        model=model_label,
        total_cases=len(results),
        passed=passed,
        failed=failed,
        pass_rate=round(passed / len(results), 4) if results else 0.0,
        avg_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        p95_latency_ms=round(p95(latencies), 2),
        total_tokens=total_tokens,
        estimated_cost_usd=total_cost,
        notes=notes,
    )

    metrics_store = store or MetricsStore()
    metrics_store.save_run(summary, results)

    csv_path = None
    if export_csv:
        csv_path = str(metrics_store.export_run_csv(summary.run_id))

    comparison = metrics_store.compare_last_two()

    return {
        "summary": asdict(summary),
        "csv_path": csv_path,
        "db_path": str(metrics_store.db_path),
        "comparison": comparison,
        "failed_case_ids": [r.case_id for r in results if not r.passed],
    }
