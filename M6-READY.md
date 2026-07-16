# M6 Ready — Streamlit dashboard

| Field | Value |
|-------|--------|
| **Date** | 2026-07-16 |
| **Status** | **Complete** |
| **Path** | `C:\Users\admin\Code\llm-eval-dashboard` |

## Delivered

- [x] `dashboard/app.py` — Streamlit UI over SQLite runs  
- [x] KPIs: pass rate, passed/total, avg + p95 latency, est. cost  
- [x] Trends: pass rate & latency charts; cost when available  
- [x] Run picker: failures table + all case scores  
- [x] Sidebar: **Run evaluation now** (golden/mock/openai)  
- [x] `pandas` + `streamlit` in requirements  

## Run

```bash
cd C:\Users\admin\Code\llm-eval-dashboard
.\.venv\Scripts\activate
pip install -r requirements.txt
set TARGET_BACKEND=golden
python scripts/run_eval.py
python -m streamlit run dashboard/app.py
```

On Windows use `python -m streamlit` (avoids broken `streamlit.exe` shim).  
Opens a local browser (typically http://localhost:8501).

## Screenshot-worthy line

> Last run: **42/42 passed** · p95 latency **~5 ms** (golden backend)

(With a live LLM, pass rate and latency will reflect real model quality.)

## Next

**M7** — Red-team subset (`redteam_cases.json` + tests).
