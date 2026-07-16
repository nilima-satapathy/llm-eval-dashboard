"""
M6 — Streamlit dashboard over eval runs stored in SQLite.

Run from repo root:
  python -m streamlit run dashboard/app.py

(On Windows, avoid bare `streamlit run` — the .exe shim often fails.)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.free_quota import build_quota_snapshot  # noqa: E402
from src.metrics_store import DEFAULT_DB, MetricsStore  # noqa: E402
from src.runners import run_evaluation  # noqa: E402

st.set_page_config(
    page_title="LLM Eval Dashboard",
    page_icon="✅",
    layout="wide",
)


def get_store() -> MetricsStore:
    return MetricsStore(db_path=DEFAULT_DB)


def runs_df(store: MetricsStore, limit: int = 50) -> pd.DataFrame:
    rows = store.list_runs(limit=limit)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Chronological for charts
    if "finished_at" in df.columns:
        df = df.sort_values("finished_at")
    return df


def results_df(store: MetricsStore, run_id: str) -> pd.DataFrame:
    rows = store.results_for_run(run_id)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def render_free_tokens_bar(store: MetricsStore) -> None:
    """Sidebar: daily free cloud quota (full bar = budget left today)."""
    snap = build_quota_snapshot(store)
    cfg = snap["config"]
    remaining = max(0, snap["advice"].remaining_tokens_today)
    limit = max(1, cfg.daily_tokens)
    frac_left = min(1.0, remaining / limit)
    st.caption("Free cloud quota (today)")
    st.progress(
        frac_left,
        text=f"{remaining:,} / {limit:,} tokens left · resets daily",
    )
    if remaining <= 0:
        st.caption("Quota empty — use **golden** / **mock** until tomorrow.")
    elif frac_left < 0.1:
        st.caption("Almost empty — prefer **golden** / **mock** or Quick run.")


def main() -> None:
    st.title("LLM Evaluation Dashboard")
    st.caption(
        "Golden-set quality gates for a software testing assistant — "
        "pass rate, failures, latency, and cost trends."
    )

    store = get_store()

    with st.sidebar:
        st.header("Controls")
        backend = st.selectbox(
            "Run backend",
            options=["golden", "mock", "openai"],
            index=0,
            help="golden = offline reference answers; openai needs API keys",
        )
        run_subset = st.checkbox("Quick run (4 seed cases only)", value=False)

        render_free_tokens_bar(store)

        if st.button("▶ Run evaluation now", type="primary"):
            with st.spinner("Running evaluation…"):
                ids = (
                    ["qa-001", "qa-002", "qa-004", "qa-007"] if run_subset else None
                )
                try:
                    out = run_evaluation(
                        backend=backend,
                        case_ids=ids,
                        store=store,
                        notes="dashboard-trigger",
                        export_csv=True,
                    )
                    st.success(
                        f"Run {out['summary']['run_id']}: "
                        f"{out['summary']['passed']}/{out['summary']['total_cases']} passed "
                        f"({out['summary']['pass_rate']:.0%})"
                    )
                    if out.get("csv_path"):
                        st.caption(f"CSV: {out['csv_path']}")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Run failed: {exc}")
            st.rerun()

        st.divider()
        st.caption("must_include ≥ 0.70 · reference_overlap ≥ 0.85")

    df_runs = runs_df(store)
    if df_runs.empty:
        st.info(
            "No runs yet. Click **Run evaluation now** in the sidebar "
            "(backend: golden) or run: `python scripts/run_eval.py`"
        )
        return

    latest = store.latest_run()
    assert latest is not None

    # —— KPI row ——
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Latest pass rate", f"{float(latest['pass_rate']):.0%}")
    c2.metric("Passed / total", f"{latest['passed']} / {latest['total_cases']}")
    c3.metric("Avg latency", f"{float(latest['avg_latency_ms']):.1f} ms")
    c4.metric("p95 latency", f"{float(latest['p95_latency_ms']):.1f} ms")
    cost = latest.get("estimated_cost_usd")
    c5.metric(
        "Est. cost (run)",
        f"${float(cost):.4f}" if cost is not None else "n/a",
    )

    cmp = store.compare_last_two()
    if cmp:
        delta = cmp["pass_rate_delta"]
        st.caption(
            f"vs previous run: pass rate **{delta:+.1%}** "
            f"({cmp['older_run_id'][:8]}… → {cmp['newer_run_id'][:8]}…)"
        )

    st.divider()

    # —— Trends ——
    left, right = st.columns(2)
    with left:
        st.subheader("Pass rate over runs")
        chart = df_runs[["finished_at", "pass_rate"]].copy()
        chart = chart.set_index("finished_at")
        st.line_chart(chart, height=280)
    with right:
        st.subheader("Latency over runs (avg & p95)")
        lat = df_runs[["finished_at", "avg_latency_ms", "p95_latency_ms"]].copy()
        lat = lat.set_index("finished_at")
        st.line_chart(lat, height=280)

    if df_runs["estimated_cost_usd"].notna().any():
        st.subheader("Estimated cost over runs (USD)")
        cost_df = df_runs[["finished_at", "estimated_cost_usd"]].dropna()
        cost_df = cost_df.set_index("finished_at")
        st.line_chart(cost_df, height=220)

    st.divider()

    # —— Run picker + details ——
    st.subheader("Run details")
    # Newest first for selectbox
    run_options = store.list_runs(limit=50)
    labels = {
        r["run_id"]: (
            f"{r['finished_at']} · {r['run_id']} · "
            f"{r['passed']}/{r['total_cases']} · {r['backend']}"
        )
        for r in run_options
    }
    selected = st.selectbox(
        "Select run",
        options=[r["run_id"] for r in run_options],
        format_func=lambda rid: labels.get(rid, rid),
    )

    run_meta = store.get_run(selected)
    res = results_df(store, selected)

    if run_meta:
        m1, m2, m3 = st.columns(3)
        m1.write(f"**Backend:** {run_meta['backend']}")
        m2.write(f"**Model:** {run_meta['model']}")
        m3.write(f"**Notes:** {run_meta.get('notes') or '—'}")

    if res.empty:
        st.warning("No per-case rows for this run.")
        return

    failed = res[res["passed"] == 0]
    st.markdown(f"**Failures:** {len(failed)} / {len(res)}")

    if not failed.empty:
        st.error("Failed cases")
        show_cols = [
            c
            for c in [
                "case_id",
                "must_include_score",
                "reference_overlap_score",
                "latency_ms",
                "error",
                "question",
                "answer",
            ]
            if c in failed.columns
        ]
        st.dataframe(failed[show_cols], use_container_width=True, hide_index=True)

    st.markdown("**All case results**")
    table_cols = [
        c
        for c in [
            "case_id",
            "passed",
            "must_include_score",
            "reference_overlap_score",
            "latency_ms",
            "total_tokens",
            "estimated_cost_usd",
            "model",
        ]
        if c in res.columns
    ]
    st.dataframe(res[table_cols], use_container_width=True, hide_index=True)

    with st.expander("Raw answer preview (selected failed or first case)"):
        preview = failed.iloc[0] if not failed.empty else res.iloc[0]
        st.write(f"**{preview['case_id']}** — {preview['question']}")
        st.text(preview.get("answer") or "(empty)")

    st.divider()
    st.subheader("Run history")
    hist_cols = [
        c
        for c in [
            "finished_at",
            "run_id",
            "backend",
            "total_cases",
            "passed",
            "failed",
            "pass_rate",
            "avg_latency_ms",
            "p95_latency_ms",
            "estimated_cost_usd",
            "notes",
        ]
        if c in df_runs.columns
    ]
    st.dataframe(
        df_runs.sort_values("finished_at", ascending=False)[hist_cols],
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()
