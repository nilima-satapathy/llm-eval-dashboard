# LLM Evaluation Dashboard

[![CI](https://github.com/nilima-satapathy/llm-eval-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/nilima-satapathy/llm-eval-dashboard/actions/workflows/ci.yml)

**Portfolio project — AI Test Engineer / GenAI quality**  
**Owner:** [Nilima Satapathy](https://github.com/nilima-satapathy)  
**Status:** M1–M8 complete · **Project 5 Quality Gate** shipped

Golden-set + red-team evaluation harness for a **software testing assistant**, with offline metrics, run storage, a Streamlit dashboard, and a **CI quality gate** that fails PRs when policy thresholds regress. Optional live model via any **OpenAI-compatible API** (e.g. Groq free tier).

---

## Why this project

Most demos show a chatbot. This project shows **how you measure one — and how you gate releases**:

| Capability | What you can point to |
|------------|------------------------|
| Golden dataset design | 42 quality cases with reference answers + must-include gates |
| Offline metrics | `must_include`, `reference_overlap`, forbidden-phrase checks |
| Live model eval | Groq / OpenAI-compatible SUT with looser live thresholds |
| Red-team / policy | 12 adversarial cases (jailbreak, secrets, off-scope, injection) |
| **Quality gate (P5)** | `gate/policy.yaml` + `scripts/run_gate.py` — CI fails on regression |
| Observability | Latency, tokens, rough cost, free-tier quota bar |
| Engineering hygiene | Pytest suite, GitHub Actions CI, SQLite + CSV history |

---

## Architecture (interview view)

```text
┌──────────────────┐     complete(question)     ┌─────────────────────┐
│ Golden / red-team│ ─────────────────────────► │ SUT backend         │
│ cases (JSON)     │                            │ mock | golden | LLM │
└────────┬─────────┘                            └──────────┬──────────┘
         │                                                 │ answer
         ▼                                                 ▼
┌──────────────────┐                            ┌─────────────────────┐
│ Offline metrics  │ ◄──── score ───────────────│ runners.evaluate    │
│ must_include     │                            └──────────┬──────────┘
│ overlap / policy │                                       │
└──────────────────┘                                       ▼
                                                ┌─────────────────────┐
                                                │ SQLite + CSV        │
                                                │ Streamlit dashboard │
                                                └─────────────────────┘
```

**Backends**

| Backend | Answers from | Use when |
|---------|--------------|----------|
| `golden` | Written `reference_answer` | Demos, CI, prove the harness |
| `mock` | Placeholder text | Show failures UI |
| `openai` | Live API (Groq, OpenAI, Ollama, …) | Real model quality |

---

## Quick start

```bash
git clone https://github.com/nilima-satapathy/llm-eval-dashboard.git
cd llm-eval-dashboard
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows; or: cp .env.example .env
```

### Offline eval + dashboard (no API key)

```bash
python scripts/run_eval.py --backend golden --suite golden
python scripts/run_eval.py --backend golden --suite red_team
python -m streamlit run dashboard/app.py
```

Open **http://localhost:8501**

### Live model (optional — Groq free tier)

1. Create a key at [console.groq.com/keys](https://console.groq.com/keys)  
2. Put it in `.env` (never commit `.env`):

```env
TARGET_BACKEND=openai
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=gsk_...
OPENAI_MODEL=llama-3.1-8b-instant
```

3. Prefer **Quick run** in the dashboard to save free quota.

More free options: [docs/FREE_AI.md](docs/FREE_AI.md)

---

## Suites & metrics

| Suite | File | Cases | Pass idea |
|-------|------|-------|-----------|
| **Quality** | `golden_dataset/qa_pairs.json` | 42 | Concepts present + reference similarity |
| **Red-team** | `golden_dataset/red_team_cases.json` | 12 | Safe refusal; no attack compliance |

| Metric | Role |
|--------|------|
| `must_include` | Required phrases / concepts (soft match for live paraphrase) |
| `reference_overlap` | Jaccard vs golden reference (strict for golden; looser for live) |
| `must_not_include` | Forbidden / attack-compliance phrases |
| Free cloud quota bar | Daily token budget remaining (sidebar) |

```bash
# Full offline pytest (CI-equivalent)
pytest tests/ -q -m "not deepeval"

# CLI
python scripts/run_eval.py --suite golden
python scripts/run_eval.py --suite red_team
python scripts/run_eval.py --suite all --backend golden
```

DeepEval answer-relevancy is **opt-in** (`RUN_DEEPEVAL=1` + judge key). See `tests/test_answer_relevancy.py`.

---

## Dashboard features

- Run **quality**, **red-team**, or **all** from the sidebar  
- Backends: golden / mock / openai  
- Progress bar during long live runs  
- Failures table + **per-case answer preview**  
- Run history table  
- Trends: pass rate, latency, cost (below history)  
- Free cloud quota (today) bar  

---

## Project layout

```text
llm-eval-dashboard/
├── .github/workflows/ci.yml     # M8 CI
├── dashboard/app.py             # Streamlit UI
├── golden_dataset/
│   ├── qa_pairs.json            # 42 quality cases
│   ├── red_team_cases.json      # 12 adversarial cases
│   └── schema.json
├── src/
│   ├── target_app.py            # SUT clients
│   ├── metrics_basic.py         # Offline metrics
│   ├── runners.py               # Eval loop + store
│   ├── metrics_store.py         # SQLite + CSV
│   ├── dataset.py
│   └── free_quota.py
├── scripts/run_eval.py
├── tests/
├── docs/FREE_AI.md
├── docs/RED_TEAM.md
└── requirements.txt
```

---

## Milestone status

| ID | Milestone | Status |
|----|-----------|--------|
| M1 | Golden dataset schema + seed cases | **Done** |
| M2 | Target app client | **Done** |
| M3 | Metrics green in Pytest | **Done** |
| M4 | 40+ cases + second metric | **Done** |
| M5 | Latency/cost + run store | **Done** |
| M6 | Streamlit dashboard | **Done** |
| M7 | Red-team subset | **Done** |
| M8 | CI + recruiter README | **Done** |

---

## Quality gate (Project 5)

Policy-driven **release gate** — fails CI when pass rate or safety thresholds regress.

```bash
python scripts/run_gate.py --profile pr      # PR smoke (default, offline)
python scripts/run_gate.py --profile full    # all golden + red-team cases
python scripts/run_gate.py --profile pr --backend mock   # force FAIL demo
```

| Profile | Use | Backend |
|---------|-----|---------|
| `pr` | Every PR / push | golden (free) |
| `full` | Nightly / manual | golden |
| `live` | Optional | openai (needs key) |

Docs: [docs/QUALITY_GATE.md](docs/QUALITY_GATE.md) · policy: `gate/policy.yaml`

## CI

On every push/PR to `master`/`main`:

1. Install Python 3.12 + dependencies  
2. `pytest tests/ -m "not deepeval"` with `TARGET_BACKEND=golden`  
3. Smoke `run_eval.py` for quality + red-team subsets  
4. **`python scripts/run_gate.py --profile pr`** — exit non-zero blocks merge  
5. Upload gate report artifacts  

No API keys required in CI.

---

## Interview one-liners

> “I built a golden-set and red-team eval harness for a testing assistant—not a chatbot demo, a measurement system.”

> “Golden proves the pipeline offline; live Groq shows real model gaps; red-team checks policy boundaries.”

> “Results land in SQLite and Streamlit so I can compare runs, inspect failures, and watch free-tier quota.”

---

## License / scope

Portfolio project for interview demos. Not multi-tenant production SaaS.  
Secrets stay in `.env` (gitignored).
