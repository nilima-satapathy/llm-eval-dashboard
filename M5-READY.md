# M5 Ready — Persist evaluation runs

| Field | Value |
|-------|--------|
| **Date** | 2026-07-16 |
| **Status** | **Complete** |
| **Path** | `C:\Users\admin\Code\llm-eval-dashboard` |

## Delivered

| Piece | Role |
|-------|------|
| `src/metrics_store.py` | SQLite store (`data/eval_runs.sqlite3`) + CSV export |
| `src/runners.py` | Run suite, score cases, save run |
| `scripts/run_eval.py` | CLI entrypoint |
| `tests/test_metrics_store.py` | Persistence + compare last two runs |

### Per case stored

- must_include_score, reference_overlap_score, passed  
- latency_ms  
- prompt/completion/total tokens (when available)  
- estimated_cost_usd (from tokens × `ESTIMATED_USD_PER_1M_TOKENS`)  

### Per run stored

- pass_rate, avg + p95 latency, total tokens/cost, backend/model  

## Run

```bash
cd C:\Users\admin\Code\llm-eval-dashboard
.\.venv\Scripts\activate
set TARGET_BACKEND=golden
python scripts/run_eval.py
```

Outputs:

- SQLite: `data/eval_runs.sqlite3`  
- CSV: `reports/run_<id>.csv`  

## Tests

```bash
pytest tests/ -v
```

## Next

**M6** — Streamlit dashboard over stored runs (pass rate, failures, latency, cost, trends).
