# Project 5 — LLM Quality Gate

Policy-driven **release gate** on top of the Project 4 eval harness.

## What it does

1. Load `gate/policy.yaml` (profile: `pr` | `full` | `live`)  
2. Run golden / red-team evals via `run_evaluation`  
3. Apply pass-rate and latency thresholds  
4. Optionally compare to a saved baseline  
5. Write `reports/gate_*.md` + `.json`  
6. Exit **0** (green) or **1** (red) so CI can block merges  

## Quick start

```powershell
cd C:\Users\admin\Code\llm-eval-dashboard
.\.venv\Scripts\activate

# Green path (offline)
python scripts/run_gate.py --profile pr

# Force fail (mock backend)
python scripts/run_gate.py --profile pr --backend mock

# Full offline suites
python scripts/run_gate.py --profile full
```

## Profiles

| Profile | When | Backend | Cases |
|---------|------|---------|--------|
| `pr` (default) | Every PR / push | golden | 4 quality + 4 red-team |
| `full` | Nightly / manual | golden | All cases |
| `live` | Optional, needs API key | openai | Small quality smoke |

Override profile: `$env:GATE_PROFILE="full"`

## How a QA extends the suite

1. Add cases to `golden_dataset/qa_pairs.json` or `red_team_cases.json`  
2. Optionally list new IDs under `case_ids` in `gate/policy.yaml`  
3. Adjust `min_pass_rate` / latency budgets in policy — **not** in CI YAML  
4. Re-run `python scripts/run_gate.py`  

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Gate passed |
| 1 | Policy failed (pass rate / latency / baseline) |
| 2 | Config / no suites / load error |

## CI

`.github/workflows/ci.yml` runs the PR smoke gate after offline pytest and uploads report artifacts.

## Interview one-liner

> “I wired golden-set and red-team evals into a **quality gate** — CI fails the PR when pass rate or safety thresholds regress, without needing paid APIs on the default path.”
