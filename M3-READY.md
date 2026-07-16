# M3 Ready — First metrics green in Pytest

| Field | Value |
|-------|--------|
| **Date** | 2026-07-16 |
| **Status** | **Complete** |
| **Path** | `C:\Users\admin\Code\llm-eval-dashboard` |

## Delivered

| Piece | Role |
|-------|------|
| `src/target_app.py` → **GoldenTarget** | Offline SUT returns `reference_answer` |
| `src/metrics_basic.py` | `must_include` coverage (offline gate) |
| `src/dataset.py` | Load golden cases |
| `tests/test_must_include.py` | Always-green offline metrics |
| `tests/test_answer_relevancy.py` | **DeepEval AnswerRelevancy** (needs judge API key) |
| `pytest.ini` | markers + pythonpath |

## Run (offline — no API key)

```bash
cd C:\Users\admin\Code\llm-eval-dashboard
.\.venv\Scripts\activate
pip install -r requirements.txt
set TARGET_BACKEND=golden
pytest tests/test_must_include.py -v
```

## Run DeepEval (optional — needs key)

```bash
set OPENAI_API_KEY=...
set TARGET_BACKEND=golden
pytest tests/test_answer_relevancy.py -v
```

With golden SUT, answers are high quality; the **judge** still bills tokens.

## Exit criteria

- [x] Pytest suite exists and passes offline (`must_include`)
- [x] DeepEval AnswerRelevancy wired (skip without key)
- [x] Target returns answer + latency for eval harness
- [x] Seed subset of golden cases exercised

## Next

**M4** — Expand to 40+ cases + second metric (e.g. faithfulness if context added).
