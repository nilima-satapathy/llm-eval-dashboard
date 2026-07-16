# Free (or near-free) AI with this dashboard

Your dashboard has **two places** AI can appear:

| Role | What it does | Free options |
|------|----------------|--------------|
| **SUT (backend)** | Answers golden questions | **Ollama (local)** · free API tiers · or skip with `golden` |
| **Judge (DeepEval)** | Scores “answer relevancy” | Optional; needs a key; skip offline |

You can demo the full UI **with zero paid API cost** using `golden` or **Ollama**.

---

## Option A — No AI API at all (already free)

```powershell
cd C:\Users\admin\Code\llm-eval-dashboard
.\.venv\Scripts\activate
set TARGET_BACKEND=golden
python scripts/run_eval.py
python -m streamlit run dashboard/app.py
```

In the sidebar: **Run backend = golden** → **Run evaluation now**.

| Backend | Cost | Real AI? |
|---------|------|----------|
| **golden** | Free | No — returns your written reference answers (best for demos & CI) |
| **mock** | Free | No — placeholder text (many metrics fail; smoke only) |

Use **golden** for interviews when you want a green dashboard without spending money.

---

## Option B — Free real AI on your PC (Ollama) ⭐ recommended free path

[Ollama](https://ollama.com/) runs models **locally** — no per-token bill.

### 1. Install Ollama

1. Download: https://ollama.com/download  
2. Install and open it (system tray on Windows).

### 2. Pull a small free model

```powershell
ollama pull llama3.2
# or: ollama pull phi3
# or: ollama pull mistral
```

### 3. Configure this project

```powershell
cd C:\Users\admin\Code\llm-eval-dashboard
copy .env.example .env
```

Edit `.env`:

```env
TARGET_BACKEND=openai
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama3.2
```

(`openai` here means “OpenAI-compatible API”, not “pay OpenAI”.)

### 4. Smoke one question

```powershell
.\.venv\Scripts\activate
python scripts/smoke_target.py --id qa-002 --backend openai
```

### 5. Full eval + dashboard

```powershell
python scripts/run_eval.py --backend openai
python -m streamlit run dashboard/app.py
```

In the sidebar choose **openai** (it will hit Ollama via the base URL).

**Note:** Local models can be slow and pass rates will be **lower than golden** (that’s realistic). Use a **Quick run (4 cases)** first.

---

## Free-tier usage on the dashboard

The Streamlit app shows **Free tier usage** (requests & tokens today vs budget) so you can decide whether to run **openai**, **Quick run (4 cases)**, or stay on **golden**.

- Counted only from **this project's** stored `openai` runs (SQLite), not your whole Groq account
- Defaults match Groq free tier for `llama-3.1-8b-instant` (override in `.env`):

```env
FREE_TIER_PROVIDER=groq
FREE_TIER_DAILY_REQUESTS=14400
FREE_TIER_DAILY_TOKENS=500000
FREE_TIER_RPM=30
FREE_TIER_TPM=6000
```

Status colors: green under 70% · yellow at 70%+ · red at 90%+ of the higher of request/token daily use.

---

## Option C — Free cloud API tiers (internet required)

These often have **free monthly quotas** (limits change — check each site):

| Provider | Typical free use | Base URL idea | Model examples |
|----------|------------------|---------------|----------------|
| **Groq** | Free tier (fast) | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant` |
| **Google AI Studio (Gemini)** | Free tier | Use their OpenAI-compatible endpoint if available, or adapt later | Gemini Flash |
| **OpenRouter** | Some free models | `https://openrouter.ai/api/v1` | check free models list |
| **GitHub Models** | Free tier with account | GitHub docs | small models |

### Example: Groq (free tier)

1. Create account → API key: https://console.groq.com/  
2. `.env`:

```env
TARGET_BACKEND=openai
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=gsk_your_groq_key
OPENAI_MODEL=llama-3.1-8b-instant
```

3. Same commands as Ollama (`run_eval` / dashboard with backend **openai**).

**Watch usage** so you stay in the free tier.

---

## DeepEval “Answer Relevancy” (optional judge)

`tests/test_answer_relevancy.py` uses an **LLM as judge** → usually needs a cloud key.

| Goal | What to do |
|------|------------|
| Free offline CI | Don’t set a key → tests **skip** (already designed this way) |
| Free-ish judge | Point DeepEval’s model env to Groq/Ollama if you configure it (advanced) |
| Default | Rely on **must_include** + **reference_overlap** (fully free) |

You do **not** need DeepEval for the Streamlit dashboard KPIs.

---

## What to use when

| Situation | Setting |
|-----------|---------|
| Interview demo, no setup | **golden** |
| Show “real model answers” free | **Ollama** + backend **openai** |
| Cloud free tier | **Groq** (or similar) + backend **openai** |
| Paid production-like | OpenAI / xAI paid keys |

---

## Dashboard checklist (free real AI)

1. Install Ollama + `ollama pull llama3.2`  
2. Set `.env` as in Option B  
3. `python scripts/run_eval.py --backend openai`  
4. `python -m streamlit run dashboard/app.py`  
5. Inspect pass rate (will be imperfect — good for storytelling)

---

## Interview talking point

> “I can run the suite offline against golden answers for regression of the *harness*, and against a free local model (Ollama) or a free API tier to score a *real* assistant. Metrics and history stay the same — only the SUT changes.”
