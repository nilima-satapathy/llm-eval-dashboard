# M2 Ready — Target app client

| Field | Value |
|-------|--------|
| **Date** | 2026-07-16 |
| **Status** | **Complete** |
| **Path** | `C:\Users\admin\Code\llm-eval-dashboard` |

## Delivered

- [x] `src/target_app.py` — `TargetResponse`, `MockTarget`, `OpenAICompatibleTarget`, `get_target()`, `ask()`
- [x] `scripts/smoke_target.py` — smoke one golden case or custom prompt
- [x] `requirements.txt` (requests, python-dotenv)
- [x] `.env.example`
- [x] Default backend **mock** (no API key needed)

## Smoke (offline)

```bash
cd C:\Users\admin\Code\llm-eval-dashboard
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python scripts/smoke_target.py --id qa-002
```

## Live LLM (optional)

```bash
copy .env.example .env
# set TARGET_BACKEND=openai and OPENAI_API_KEY=...
python scripts/smoke_target.py --id qa-001 --backend openai
```

## Exit criteria

- [x] One call: prompt → answer (+ latency_ms)
- [x] Works offline via mock
- [x] Optional real model via OpenAI-compatible API
- [x] No DeepEval yet (M3)

## Next

**M3** — First DeepEval metric green in Pytest (e.g. faithfulness or relevancy on seed set).
