# LLM Evaluation Dashboard

> Signature AI QA project — golden-set evaluation for an LLM / RAG system  
> **Owner:** Nilima Satapathy  
> **Status:** M1 complete (schema + 10 seed cases). Metrics start M3.

## What this will become

A Pytest + DeepEval suite over a **golden dataset**, with latency/cost logging, a Streamlit dashboard, red-team cases, and CI smoke runs.  
Target system: a testing-domain assistant (or DocQ RAG in later milestones).

## Milestone status

| ID | Milestone | Status |
|----|-----------|--------|
| **M1** | Golden dataset schema + 10 seed cases | **Done** |
| M2 | Target app client | Pending |
| M3 | First DeepEval metric in Pytest | Pending |
| M4 | 40+ cases + second metric | Pending |
| M5 | Latency/cost + run store | Pending |
| M6 | Streamlit dashboard | Pending |
| M7 | Red-team subset | Pending |
| M8 | CI + recruiter README polish | Pending |

## M1 deliverables

```
llm-eval-dashboard/
├── README.md
├── .gitignore
├── docs/
│   └── GOLDEN_DATASET_SCHEMA.md
└── golden_dataset/
    ├── schema.json          # JSON Schema
    └── qa_pairs.json        # 10 seed cases (software testing assistant)
```

### Domain

**software_testing_assistant** — questions a QA/SDET might ask (concepts, strategy, API, automation, process).

### Cases (seed)

| ID | Category | Difficulty | Topic |
|----|----------|------------|--------|
| qa-001 | concepts | easy | Verification vs validation |
| qa-002 | concepts | easy | Flaky tests |
| qa-003 | strategy | medium | Risk-based prioritization |
| qa-004 | automation | medium | Page Object Model |
| qa-005 | api | medium | API asserts beyond 200 |
| qa-006 | process | medium | Severity vs priority |
| qa-007 | strategy | hard | LLM testing vs classical regression |
| qa-008 | tooling | easy | Why CI on PRs |
| qa-009 | automation | hard | When not to automate |
| qa-010 | api | hard | Negative login API design |

## Validate JSON (optional)

If you have `check-jsonschema` or similar:

```bash
# example with Python json module
python -c "import json; json.load(open('golden_dataset/qa_pairs.json')); print('ok', len(json.load(open('golden_dataset/qa_pairs.json'))['cases']), 'cases')"
```

## Not in M1

- No `requirements.txt` metrics stack yet  
- No Pytest / DeepEval  
- No Streamlit  
- No API keys  

## Local path (not OneDrive)

```
C:\Users\admin\Code\llm-eval-dashboard
```

## Spec source

Career plan (may still live under OneDrive Code):  
`...\AI-Career-Plan\04-projects\project-04-llm-eval-dashboard\SPEC.md`

## Next

**M2:** `src/target_app.py` — thin client that returns an answer for a prompt (LLM or RAG).
