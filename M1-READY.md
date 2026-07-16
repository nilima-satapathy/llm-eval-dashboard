# M1 Ready — Golden dataset schema + 10 seeds

| Field | Value |
|-------|--------|
| **Date** | 2026-07-16 |
| **Status** | **Complete** |
| **Repo** | `C:\Users\admin\Code\llm-eval-dashboard` (local disk, not OneDrive) |

## Delivered

- [x] JSON Schema: `golden_dataset/schema.json`
- [x] Human docs: `docs/GOLDEN_DATASET_SCHEMA.md`
- [x] Seed set: `golden_dataset/qa_pairs.json` (**10** cases)
- [x] Domain: software testing assistant
- [x] No metrics / target client (correctly deferred)

## Exit criteria

- [x] Schema documents required fields  
- [x] 10 cases with `must_include` / `must_not_include`  
- [x] Mix of categories and difficulties  
- [x] JSON loads cleanly  

## Next

**M2 — Target app client** (`src/target_app.py`)
