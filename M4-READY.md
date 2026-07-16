# M4 Ready — 40+ cases + second metric

| Field | Value |
|-------|--------|
| **Date** | 2026-07-16 |
| **Status** | **Complete** |
| **Path** | `C:\Users\admin\Code\llm-eval-dashboard` |

## Delivered

- [x] Golden set expanded to **42 cases** (`qa-001` … `qa-042`)
- [x] **Metric 1:** `must_include` (coverage of required concepts)
- [x] **Metric 2:** `reference_overlap` (token Jaccard vs reference answer)
- [x] Pytest runs both metrics on the full set (offline with `TARGET_BACKEND=golden`)
- [x] Dataset size guard: `>= 40` cases
- [x] Helper: `scripts/build_m4_cases.py` (used to append cases)

## Run

```bash
cd C:\Users\admin\Code\llm-eval-dashboard
.\.venv\Scripts\activate
set TARGET_BACKEND=golden
pytest tests/ -v
```

## Metrics summary

| Metric | Type | Threshold (tests) | Needs API key? |
|--------|------|-------------------|----------------|
| must_include | Offline keyword coverage | ≥ 0.70 | No |
| reference_overlap | Offline Jaccard vs reference | ≥ 0.85 | No |
| Answer relevancy (DeepEval) | LLM judge | ≥ 0.50 | Yes (optional) |

## Next

**M5** — Persist run results (latency/cost/scores to CSV or SQLite) via `metrics_store.py`.
