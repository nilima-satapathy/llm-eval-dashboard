# LLM Evaluation Dashboard

> Signature AI QA project — golden-set evaluation for an LLM / RAG system  
> **Owner:** Nilima Satapathy  
> **Status:** M1–M2 complete. Metrics start M3.

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
| M3 | First DeepEval metric in Pytest | Pending |
| M4 | 40+ cases + second metric | Pending |
| M5 | Latency/cost + run store | Pending |
| M6 | Streamlit dashboard | Pending |
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
│   └── target_app.py        # SUT client (M2)
└── scripts/
    └── smoke_target.py
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
| `mock` (default) | Deterministic placeholder answer; no key |
| `openai` | Chat Completions (`OPENAI_BASE_URL` + `OPENAI_API_KEY` or `XAI_API_KEY`) |

## M1 — golden set

Domain **software_testing_assistant** — 10 cases in `golden_dataset/qa_pairs.json`.

## Spec source

`AI-Career-Plan/04-projects/project-04-llm-eval-dashboard/SPEC.md`

## Next

**M3:** Wire DeepEval (e.g. answer relevancy) in Pytest against `get_target().complete()`.
