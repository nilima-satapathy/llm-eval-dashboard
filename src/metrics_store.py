"""
M5 — Persist evaluation runs (SQLite + optional CSV export).

Schema:
  runs     — one suite execution
  results  — one row per golden case in that run
"""

from __future__ import annotations

import csv
import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "eval_runs.sqlite3"
DEFAULT_REPORTS = ROOT / "reports"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class CaseResult:
    case_id: str
    question: str
    answer: str
    passed: bool
    must_include_score: float
    reference_overlap_score: float
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None
    model: str = ""
    backend: str = ""
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunSummary:
    run_id: str
    started_at: str
    finished_at: str
    backend: str
    model: str
    total_cases: int
    passed: int
    failed: int
    pass_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens: int | None
    estimated_cost_usd: float | None
    notes: str = ""


class MetricsStore:
    """SQLite-backed store for eval runs and per-case results."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    model TEXT NOT NULL,
                    total_cases INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    failed INTEGER NOT NULL,
                    pass_rate REAL NOT NULL,
                    avg_latency_ms REAL NOT NULL,
                    p95_latency_ms REAL NOT NULL,
                    total_tokens INTEGER,
                    estimated_cost_usd REAL,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    must_include_score REAL NOT NULL,
                    reference_overlap_score REAL NOT NULL,
                    latency_ms REAL NOT NULL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    estimated_cost_usd REAL,
                    model TEXT,
                    backend TEXT,
                    error TEXT,
                    details_json TEXT,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id)
                );

                CREATE INDEX IF NOT EXISTS idx_results_run ON results(run_id);
                CREATE INDEX IF NOT EXISTS idx_results_case ON results(case_id);
                """
            )

    def save_run(
        self,
        summary: RunSummary,
        results: list[CaseResult],
    ) -> str:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, started_at, finished_at, backend, model,
                    total_cases, passed, failed, pass_rate,
                    avg_latency_ms, p95_latency_ms, total_tokens,
                    estimated_cost_usd, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary.run_id,
                    summary.started_at,
                    summary.finished_at,
                    summary.backend,
                    summary.model,
                    summary.total_cases,
                    summary.passed,
                    summary.failed,
                    summary.pass_rate,
                    summary.avg_latency_ms,
                    summary.p95_latency_ms,
                    summary.total_tokens,
                    summary.estimated_cost_usd,
                    summary.notes,
                ),
            )
            for r in results:
                conn.execute(
                    """
                    INSERT INTO results (
                        run_id, case_id, question, answer, passed,
                        must_include_score, reference_overlap_score, latency_ms,
                        prompt_tokens, completion_tokens, total_tokens,
                        estimated_cost_usd, model, backend, error, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        summary.run_id,
                        r.case_id,
                        r.question,
                        r.answer,
                        1 if r.passed else 0,
                        r.must_include_score,
                        r.reference_overlap_score,
                        r.latency_ms,
                        r.prompt_tokens,
                        r.completion_tokens,
                        r.total_tokens,
                        r.estimated_cost_usd,
                        r.model,
                        r.backend,
                        r.error,
                        json.dumps(r.details, ensure_ascii=False),
                    ),
                )
        return summary.run_id

    def latest_run(self) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM runs ORDER BY finished_at DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY finished_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def results_for_run(self, run_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM results WHERE run_id = ? ORDER BY case_id",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def compare_last_two(self) -> dict[str, Any] | None:
        """Return pass-rate delta between the two most recent runs, if any."""
        runs = self.list_runs(limit=2)
        if len(runs) < 2:
            return None
        newer, older = runs[0], runs[1]
        return {
            "newer_run_id": newer["run_id"],
            "older_run_id": older["run_id"],
            "newer_pass_rate": newer["pass_rate"],
            "older_pass_rate": older["pass_rate"],
            "pass_rate_delta": round(
                float(newer["pass_rate"]) - float(older["pass_rate"]), 4
            ),
            "newer_avg_latency_ms": newer["avg_latency_ms"],
            "older_avg_latency_ms": older["avg_latency_ms"],
        }

    def usage_for_backend(
        self,
        *,
        backend: str = "openai",
        since_iso: str | None = None,
    ) -> dict[str, Any]:
        """
        Aggregate API usage for free-tier dashboards.

        Counts per-case rows (1 request ≈ 1 case) for the given backend,
        optionally since an ISO timestamp (compared to results via parent run).
        """
        with self._conn() as conn:
            if since_iso:
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) AS requests,
                        COALESCE(SUM(r.total_tokens), 0) AS tokens,
                        COUNT(DISTINCT r.run_id) AS runs,
                        COALESCE(SUM(r.estimated_cost_usd), 0) AS estimated_cost_usd
                    FROM results r
                    JOIN runs u ON u.run_id = r.run_id
                    WHERE LOWER(COALESCE(r.backend, u.backend, '')) = LOWER(?)
                      AND u.finished_at >= ?
                    """,
                    (backend, since_iso),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) AS requests,
                        COALESCE(SUM(r.total_tokens), 0) AS tokens,
                        COUNT(DISTINCT r.run_id) AS runs,
                        COALESCE(SUM(r.estimated_cost_usd), 0) AS estimated_cost_usd
                    FROM results r
                    JOIN runs u ON u.run_id = r.run_id
                    WHERE LOWER(COALESCE(r.backend, u.backend, '')) = LOWER(?)
                    """,
                    (backend,),
                ).fetchone()
            return {
                "backend": backend,
                "since_iso": since_iso,
                "requests": int(row["requests"] or 0),
                "tokens": int(row["tokens"] or 0),
                "runs": int(row["runs"] or 0),
                "estimated_cost_usd": float(row["estimated_cost_usd"] or 0.0),
            }

    def avg_tokens_per_case(
        self,
        *,
        backend: str = "openai",
        limit_runs: int = 10,
    ) -> float | None:
        """Mean total_tokens per case over recent openai runs (for capacity estimates)."""
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT AVG(r.total_tokens) AS avg_tok
                FROM results r
                JOIN runs u ON u.run_id = r.run_id
                WHERE LOWER(COALESCE(r.backend, u.backend, '')) = LOWER(?)
                  AND r.total_tokens IS NOT NULL
                  AND r.total_tokens > 0
                  AND u.run_id IN (
                      SELECT run_id FROM runs
                      WHERE LOWER(backend) = LOWER(?)
                      ORDER BY finished_at DESC
                      LIMIT ?
                  )
                """,
                (backend, backend, limit_runs),
            ).fetchone()
            if row is None or row["avg_tok"] is None:
                return None
            return round(float(row["avg_tok"]), 1)

    def export_run_csv(
        self,
        run_id: str,
        reports_dir: Path | None = None,
    ) -> Path:
        """Write per-case results CSV under reports/."""
        out_dir = Path(reports_dir or DEFAULT_REPORTS)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"run_{run_id}.csv"
        rows = self.results_for_run(run_id)
        if not rows:
            raise ValueError(f"No results for run_id={run_id}")
        fieldnames = list(rows[0].keys())
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def estimate_cost_usd(
    total_tokens: int | None,
    usd_per_1m_tokens: float | None = None,
) -> float | None:
    """Rough cost from total tokens (env ESTIMATED_USD_PER_1M_TOKENS, default 0.15)."""
    import os

    if total_tokens is None:
        return None
    rate = usd_per_1m_tokens
    if rate is None:
        rate = float(os.getenv("ESTIMATED_USD_PER_1M_TOKENS") or "0.15")
    return round((total_tokens / 1_000_000.0) * rate, 6)


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, int(round(0.95 * (len(ordered) - 1))))
    return ordered[idx]
