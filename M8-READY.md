# M8 READY — CI + recruiter README

**Status:** Done

## What shipped

| Item | Detail |
|------|--------|
| GitHub Actions | `.github/workflows/ci.yml` — offline pytest + CLI smoke |
| CI badge | Top of README |
| Recruiter README | Architecture, quick start, suites, interview lines |
| Deps split | `requirements.txt` (CI/runtime) · `requirements-dev.txt` (+ DeepEval) |

## CI behaviour

- Trigger: push / PR → `master` or `main`
- `TARGET_BACKEND=golden` (never burns cloud keys)
- `pytest tests/ -m "not deepeval"`
- Smoke: `run_eval.py` golden + red_team subset

## Local CI-equivalent

```powershell
cd C:\Users\admin\Code\llm-eval-dashboard
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:TARGET_BACKEND="golden"
$env:RUN_DEEPEVAL="0"
python -m pytest tests/ -q -m "not deepeval"
python scripts/run_eval.py --backend golden --suite golden --ids qa-001,qa-002 --no-csv
python scripts/run_eval.py --backend golden --suite red_team --ids rt-001,rt-002 --no-csv
```

## After first push of this milestone

Confirm the green badge at:  
https://github.com/nilima-satapathy/llm-eval-dashboard/actions
