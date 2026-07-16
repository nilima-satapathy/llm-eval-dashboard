# M7 READY — Red-team subset

**Status:** Done  
**Suite file:** `golden_dataset/red_team_cases.json` (12 cases `rt-001`…`rt-012`)  
**Docs:** `docs/RED_TEAM.md`

## What shipped

| Piece | Detail |
|-------|--------|
| Dataset | Jailbreak, malware, off-scope, secrets, SQLi, integrity, injection, PII, role abuse |
| Scoring | Policy-first: `must_include` refusal cues + no `must_not_include` attack markers; overlap informational |
| Loader | `load_cases(suite="golden"\|"red_team"\|"all")` |
| Golden SUT | Serves both quality + red-team reference answers offline |
| CLI | `python scripts/run_eval.py --suite red_team` |
| Dashboard | Suite selector: Quality / Red-team / All |
| Tests | `tests/test_red_team.py` |

## Verify

```powershell
cd C:\Users\admin\Code\llm-eval-dashboard
.\.venv\Scripts\activate
python -m pytest tests/test_red_team.py -q
python scripts/run_eval.py --backend golden --suite red_team --notes m7-verify
python -m streamlit run dashboard/app.py
```

In UI: **Suite → Red-team** → **golden** → Run.
