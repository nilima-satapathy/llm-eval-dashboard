# PROJECT 5 READY — LLM Quality Gate

**Status:** Implemented (CLI + policy + tests + CI step)  
**Repo:** `llm-eval-dashboard` (extends Project 4)

## Delivered

| Item | Path |
|------|------|
| Policy | `gate/policy.yaml` |
| Loader / decide / report / run | `gate/*.py` |
| CLI | `scripts/run_gate.py` |
| Tests | `tests/test_gate_*.py` |
| Docs | `docs/QUALITY_GATE.md` |
| CI | `ci.yml` — Quality Gate step + artifacts |

## Verify

```powershell
cd C:\Users\admin\Code\llm-eval-dashboard
.\.venv\Scripts\activate
pytest tests/test_gate_policy.py tests/test_gate_decide.py tests/test_gate_run.py -q
python scripts/run_gate.py --profile pr
python scripts/run_gate.py --profile pr --backend mock
# expect exit 1 on mock
```

## Resume line

> Built a production-style LLM quality gate on a golden/red-team eval harness — PR CI fails when pass rate or safety gates regress, offline-first with optional live model runs.
