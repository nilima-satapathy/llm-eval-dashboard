# LLM Evaluation Dashboard

> Signature AI QA project — golden-set evaluation for an LLM / RAG system  
> **Owner:** Nilima Satapathy  
> **Status:** M1–M6 complete. Red-team in M7.

## What this will become

A Pytest + DeepEval suite over a **golden dataset**, with latency/cost logging, a Streamlit dashboard, red-team cases, and CI smoke runs.  
Target system: a **software testing assistant** (mock offline, or live LLM via OpenAI-compatible API).

## Local path (not OneDrive)

```
C:\Users\admin\Code\llm-eval-dashboard
```

## Milestone status

| ID | Milestone | Status |
|----|-----------|--------|
| **M1** | Golden dataset schema + 10 seed cases | **Done** |
| **M2** | Target app client | **Done** |
| **M3** | First metrics green in Pytest | **Done** |
| **M4** | 40+ cases + second metric | **Done** |
| **M5** | Latency/cost + run store | **Done** |
| **M6** | Streamlit dashboard | **Done** |
| M7 | Red-team subset | Pending |
| M8 | CI + recruiter README polish | Pending |

## Layout

```
llm-eval-dashboard/
├── README.md
├── requirements.txt
├── .env.example
├── docs/GOLDEN_DATASET_SCHEMA.md
├── golden_dataset/
│   ├── schema.json
│   └── qa_pairs.json        # 10 seed cases
├── src/
│   ├── __init__.py
│   ├── target_app.py        # SUT: mock | golden | openai
│   ├── dataset.py
│   └── metrics_basic.py     # offline must_include
├── tests/
│   ├── conftest.py
│   ├── test_must_include.py
│   └── test_answer_relevancy.py  # DeepEval (needs API key)
├── scripts/
│   └── smoke_target.py
└── pytest.ini
```

## Setup

```bash
cd C:\Users\admin\Code\llm-eval-dashboard
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## M2 — call the target

```bash
# Offline (default)
python scripts/smoke_target.py --id qa-002

# Custom prompt
python scripts/smoke_target.py --prompt "What is regression testing?"

# Live model (needs .env)
# TARGET_BACKEND=openai OPENAI_API_KEY=... python scripts/smoke_target.py --id qa-001
```

### Backends

| `TARGET_BACKEND` | Behaviour |
|------------------|-----------|
| `mock` | Placeholder answer; smoke only |
| `golden` | Returns golden `reference_answer` (offline eval harness) |
| `openai` | Live Chat Completions |

## M3 — run metrics

```bash
# Offline (default for tests: golden SUT)
set TARGET_BACKEND=golden
pytest tests/test_must_include.py -v

# DeepEval Answer Relevancy (judge needs OPENAI_API_KEY)
set OPENAI_API_KEY=sk-...
pytest tests/test_answer_relevancy.py -v
```

## Golden set + metrics

Domain **software_testing_assistant** — **42 cases** in `golden_dataset/qa_pairs.json`.

| Metric | Module / test | Offline |
|--------|----------------|---------|
| must_include | `metrics_basic` / `test_must_include.py` | Yes |
| reference_overlap | `metrics_basic` / `test_reference_overlap.py` | Yes |
| DeepEval answer relevancy | `test_answer_relevancy.py` | Needs judge API key |

```bash
set TARGET_BACKEND=golden
pytest tests/ -v
```

## M5 — run eval and store results

```bash
set TARGET_BACKEND=golden
python scripts/run_eval.py
# → data/eval_runs.sqlite3
# → reports/run_<id>.csv
```

Stores per-case scores, latency, tokens/cost (when available), and suite pass rate / p95 latency.

## M6 — dashboard

```bash
set TARGET_BACKEND=golden
python scripts/run_eval.py          # seed DB if empty
python -m streamlit run dashboard/app.py   # http://localhost:8501
```

On Windows, prefer `python -m streamlit` (the `streamlit.exe` shim often errors).

Shows pass rate, failures, latency/cost trends, and a run picker with per-case scores. Sidebar can trigger a new eval run.

## Free AI (no paid API)

See **[docs/FREE_AI.md](docs/FREE_AI.md)**.

| Mode | Cost | How |
|------|------|-----|
| **golden** | Free | Default offline demo |
| **Ollama** (local) | Free | `OPENAI_BASE_URL=http://localhost:11434/v1` |
| **Groq** free tier | Free quota | Set Groq base URL + key |

Dashboard sidebar → backend **openai** after configuring `.env`.

## Spec source

`AI-Career-Plan/04-projects/project-04-llm-eval-dashboard/SPEC.md`

## Next

**M7:** Red-team cases + tests.
