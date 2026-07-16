# Golden dataset schema (M1)

Domain: **software testing assistant** — answers a junior/mid engineer or QA about testing concepts, strategy, and practical tooling.

## Files

| File | Purpose |
|------|---------|
| `golden_dataset/qa_pairs.json` | Main golden set (seed: 10 cases; target later: ≥40) |
| `golden_dataset/schema.json` | JSON Schema for validation |
| `golden_dataset/redteam_cases.json` | *Not in M1* — red-team cases land in M7 |

## Case object (`qa_pairs.json`)

```json
{
  "id": "string — stable unique id, e.g. qa-001",
  "domain": "software_testing_assistant",
  "category": "string — concepts | strategy | automation | api | process | tooling",
  "difficulty": "easy | medium | hard",
  "question": "string — user prompt to the system under test",
  "reference_answer": "string — high-quality expected answer (for humans + future metrics)",
  "must_include": ["string — key phrases or concepts a good answer should cover"],
  "must_not_include": ["string — hallucinations or wrong advice to avoid"],
  "context": "string | null — optional retrieved/context doc for RAG-style eval (null in M1 seeds)",
  "tags": ["string"],
  "source": "string — why this case exists (curriculum / common interview / production risk)",
  "notes": "string | null — optional grader notes"
}
```

### Field rules

| Field | Required | Rules |
|-------|----------|--------|
| `id` | yes | Unique within file; pattern `qa-NNN` |
| `question` | yes | One clear question; no multi-part laundry lists |
| `reference_answer` | yes | 2–6 sentences; factual; QA-voice; no filler |
| `must_include` | yes | 2–6 concrete concepts (used later for checks / human review) |
| `must_not_include` | yes | May be `[]`; list wrong claims we care about |
| `context` | no | `null` until RAG-targeted eval (optional later) |
| `difficulty` | yes | `easy` = definition; `medium` = trade-off; `hard` = scenario judgment |

## Top-level file shape

```json
{
  "version": "1.0",
  "domain": "software_testing_assistant",
  "description": "...",
  "cases": [ /* case objects */ ]
}
```

## What M1 does *not* include

- DeepEval / Pytest metrics  
- Target app client  
- Dashboard  
- Red-team file  

Those start **M2+**.
