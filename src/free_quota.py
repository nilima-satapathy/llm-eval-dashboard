"""
Free-tier budget helpers for the dashboard.

Tracks usage from *this project's* SQLite runs (openai backend only), then
compares against configurable free-tier limits (defaults: Groq llama-3.1-8b-instant).

Note: Groq free tier is rate-limit based (not prepaid $ credits). Limits can change;
override via .env. Account-wide usage outside this app is not visible.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.dataset import load_cases

# Defaults aligned with Groq free tier docs for llama-3.1-8b-instant
# (RPM / RPD / TPM / TPD — verify in console if limits change)
DEFAULT_PROVIDER = "groq"
DEFAULT_DAILY_REQUESTS = 14_400
DEFAULT_DAILY_TOKENS = 500_000
DEFAULT_RPM = 30
DEFAULT_TPM = 6_000
DEFAULT_MONTHLY_USD: float | None = None  # optional soft budget


@dataclass
class FreeTierConfig:
    provider: str
    daily_requests: int
    daily_tokens: int
    rpm: int
    tpm: int
    monthly_usd: float | None
    model_hint: str


@dataclass
class UsageWindow:
    label: str
    since_iso: str
    requests: int  # API calls ≈ scored cases with openai backend
    tokens: int
    runs: int
    estimated_cost_usd: float


@dataclass
class CapacityAdvice:
    avg_tokens_per_case: float | None
    full_suite_cases: int
    quick_suite_cases: int
    remaining_requests_today: int
    remaining_tokens_today: int
    full_runs_left_by_requests: int | None
    full_runs_left_by_tokens: int | None
    quick_runs_left_by_requests: int | None
    quick_runs_left_by_tokens: int | None
    status: str  # ok | caution | critical | offline
    message: str


def load_free_tier_config() -> FreeTierConfig:
    monthly_raw = (os.getenv("FREE_TIER_MONTHLY_USD") or "").strip()
    monthly: float | None
    if monthly_raw == "":
        monthly = DEFAULT_MONTHLY_USD
    else:
        monthly = float(monthly_raw)

    return FreeTierConfig(
        provider=(os.getenv("FREE_TIER_PROVIDER") or DEFAULT_PROVIDER).strip().lower(),
        daily_requests=int(
            os.getenv("FREE_TIER_DAILY_REQUESTS") or DEFAULT_DAILY_REQUESTS
        ),
        daily_tokens=int(os.getenv("FREE_TIER_DAILY_TOKENS") or DEFAULT_DAILY_TOKENS),
        rpm=int(os.getenv("FREE_TIER_RPM") or DEFAULT_RPM),
        tpm=int(os.getenv("FREE_TIER_TPM") or DEFAULT_TPM),
        monthly_usd=monthly,
        model_hint=(os.getenv("OPENAI_MODEL") or "llama-3.1-8b-instant").strip(),
    )


def _utc_today_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _utc_month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _pct(used: float, limit: float) -> float:
    if limit <= 0:
        return 0.0
    return min(100.0, round(100.0 * used / limit, 1))


def usage_status(req_pct: float, tok_pct: float) -> tuple[str, str]:
    peak = max(req_pct, tok_pct)
    if peak >= 90:
        return (
            "critical",
            "Near free-tier daily limit — prefer golden/mock or wait until UTC midnight reset.",
        )
    if peak >= 70:
        return (
            "caution",
            "Over 70% of today's free budget used — use Quick run (4 cases) when possible.",
        )
    return (
        "ok",
        "Plenty of free-tier headroom for more openai eval runs today (from this app's tracking).",
    )


def capacity_from_usage(
    *,
    today: UsageWindow,
    config: FreeTierConfig,
    avg_tokens_per_case: float | None,
    full_suite_cases: int | None = None,
    quick_suite_cases: int = 4,
) -> CapacityAdvice:
    n_full = full_suite_cases if full_suite_cases is not None else len(load_cases())
    rem_req = max(0, config.daily_requests - today.requests)
    rem_tok = max(0, config.daily_tokens - today.tokens)

    def runs_left(remaining: int, per_run: int) -> int | None:
        if per_run <= 0:
            return None
        return remaining // per_run

    full_by_req = runs_left(rem_req, n_full)
    quick_by_req = runs_left(rem_req, quick_suite_cases)

    full_by_tok: int | None = None
    quick_by_tok: int | None = None
    if avg_tokens_per_case and avg_tokens_per_case > 0:
        full_by_tok = runs_left(rem_tok, int(round(avg_tokens_per_case * n_full)))
        quick_by_tok = runs_left(
            rem_tok, int(round(avg_tokens_per_case * quick_suite_cases))
        )

    req_pct = _pct(today.requests, config.daily_requests)
    tok_pct = _pct(today.tokens, config.daily_tokens)
    status, message = usage_status(req_pct, tok_pct)

    if today.requests == 0 and today.tokens == 0:
        # No paid API usage today yet
        if status == "ok":
            message = (
                "No openai usage from this dashboard today yet. "
                "Full suite ≈ 1 request per golden case."
            )

    return CapacityAdvice(
        avg_tokens_per_case=avg_tokens_per_case,
        full_suite_cases=n_full,
        quick_suite_cases=quick_suite_cases,
        remaining_requests_today=rem_req,
        remaining_tokens_today=rem_tok,
        full_runs_left_by_requests=full_by_req,
        full_runs_left_by_tokens=full_by_tok,
        quick_runs_left_by_requests=quick_by_req,
        quick_runs_left_by_tokens=quick_by_tok,
        status=status,
        message=message,
    )


def build_quota_snapshot(store: Any) -> dict[str, Any]:
    """
    Aggregate usage from MetricsStore and return a dashboard-ready dict.

    `store` is MetricsStore (typed Any to avoid circular imports in tests).
    """
    config = load_free_tier_config()
    today_start = _utc_today_start().isoformat()
    month_start = _utc_month_start().isoformat()

    today_raw = store.usage_for_backend(backend="openai", since_iso=today_start)
    month_raw = store.usage_for_backend(backend="openai", since_iso=month_start)
    avg_tok = store.avg_tokens_per_case(backend="openai", limit_runs=10)

    today = UsageWindow(
        label="today_utc",
        since_iso=today_start,
        requests=int(today_raw["requests"]),
        tokens=int(today_raw["tokens"]),
        runs=int(today_raw["runs"]),
        estimated_cost_usd=float(today_raw["estimated_cost_usd"]),
    )
    month = UsageWindow(
        label="month_utc",
        since_iso=month_start,
        requests=int(month_raw["requests"]),
        tokens=int(month_raw["tokens"]),
        runs=int(month_raw["runs"]),
        estimated_cost_usd=float(month_raw["estimated_cost_usd"]),
    )
    advice = capacity_from_usage(
        today=today, config=config, avg_tokens_per_case=avg_tok
    )

    req_pct = _pct(today.requests, config.daily_requests)
    tok_pct = _pct(today.tokens, config.daily_tokens)
    month_usd_pct: float | None = None
    if config.monthly_usd is not None and config.monthly_usd > 0:
        month_usd_pct = _pct(month.estimated_cost_usd, config.monthly_usd)

    return {
        "config": config,
        "today": today,
        "month": month,
        "advice": advice,
        "today_request_pct": req_pct,
        "today_token_pct": tok_pct,
        "month_usd_pct": month_usd_pct,
        "disclaimer": (
            "Usage is counted only from this app's stored openai runs "
            "(not your full Groq/OpenAI account). Limits are configurable in .env."
        ),
    }
