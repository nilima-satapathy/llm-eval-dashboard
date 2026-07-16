#!/usr/bin/env python3
"""One-shot helper used during M4 to append cases qa-011..qa-042 if missing."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "golden_dataset" / "qa_pairs.json"

EXTRA = [
    ("qa-011", "concepts", "easy", "What is regression testing?",
     "Regression testing re-runs selected tests after changes to check that existing behaviour still works. It protects against unintended side effects when code, config, or dependencies change. Suites are often automated and run in CI for fast feedback.",
     ["regression", "existing", "changes", "side effects"], ["skip regression after every release"]),
    ("qa-012", "concepts", "easy", "What is smoke testing?",
     "Smoke testing is a shallow, fast set of checks that the build is stable enough for deeper testing. It covers critical launch paths (start app, login, core navigation). If smoke fails, further testing is usually blocked until the build is fixed.",
     ["smoke", "critical", "fast", "build"], ["smoke testing replaces full regression"]),
    ("qa-013", "concepts", "easy", "What is a test oracle?",
     "A test oracle is the mechanism that decides whether an observed result is correct. Oracles can be expected values, prior system behaviour, specifications, or human judgment. Without a clear oracle, automation cannot reliably pass or fail a check.",
     ["oracle", "correct", "expected"], ["oracle means only production monitoring"]),
    ("qa-014", "concepts", "medium", "What is boundary value analysis?",
     "Boundary value analysis designs tests at the edges of input ranges where defects often cluster, such as min, max, just inside, and just outside limits. It complements equivalence partitioning by focusing on edges rather than only representative middle values.",
     ["boundary", "edge", "min", "max"], ["only test mid-range values"]),
    ("qa-015", "concepts", "medium", "What is equivalence partitioning?",
     "Equivalence partitioning groups inputs that should behave the same into classes, then tests one or few values per class. This reduces redundant cases while keeping coverage of distinct behaviours, including invalid partitions for negative tests.",
     ["equivalence", "partition", "classes", "reduce"], ["test every possible input value always"]),
    ("qa-016", "strategy", "medium", "What is risk-based testing?",
     "Risk-based testing allocates effort where failure impact or likelihood is highest. Teams rank features by business criticality, change frequency, and defect history, then deepen tests on top risks first. Lower-risk areas get lighter coverage when time is limited.",
     ["risk", "impact", "priority", "coverage"], ["test only low-risk areas first"]),
    ("qa-017", "strategy", "medium", "How do you decide the test pyramid balance for a web app?",
     "Prefer many fast unit tests, fewer integration tests, and a thin UI end-to-end layer. UI tests are valuable for critical journeys but are slower and flakier, so keep them focused. APIs and services should carry most contract and business-rule checks below the UI.",
     ["unit", "integration", "UI", "critical journeys"], ["only UI end-to-end tests"]),
    ("qa-018", "strategy", "hard", "How would you plan testing for a feature behind a feature flag?",
     "Test both flag-off and flag-on behaviour, including default state for existing users. Cover rollout percentage edge cases if applicable, configuration mistakes, and cleanup when the flag is removed. Automate critical paths for both states and verify analytics or logging still make sense.",
     ["flag-on", "flag-off", "default", "rollout"], ["test only when flag is on"]),
    ("qa-019", "automation", "easy", "What is the difference between unit tests and end-to-end tests?",
     "Unit tests verify small units of code in isolation with fast feedback. End-to-end tests exercise full user flows through the real stack and catch integration issues but are slower and more brittle. Both belong in a balanced strategy.",
     ["unit", "isolation", "end-to-end", "user flows"], ["unit tests replace e2e entirely"]),
    ("qa-020", "automation", "medium", "Why is waiting for fixed sleeps a bad practice in UI automation?",
     "Hard-coded sleeps slow the suite and still fail under load variance. Prefer explicit waits for conditions such as element visible, network idle, or text present. Condition-based waits are faster when the app is quick and more reliable when it is slow.",
     ["sleep", "explicit wait", "condition", "flaky"], ["always sleep 10 seconds before every click"]),
    ("qa-021", "automation", "medium", "What artifacts help debug a failed Playwright or Selenium test in CI?",
     "Screenshots, DOM snapshots, video recordings, Playwright traces, browser console logs, and network HAR files help reproduce failures. Attach them on failure in CI so engineers can diagnose without re-running locally first.",
     ["screenshot", "trace", "logs", "CI"], ["never keep failure artifacts"]),
    ("qa-022", "automation", "hard", "How do you keep a large UI automation suite maintainable?",
     "Use page objects or screenplay patterns, stable test ids, shared fixtures, and clear data setup/teardown. Tag tests by risk and run smoke on every PR with fuller suites nightly. Quarantine flaky tests with ownership instead of silent retries forever. Review suite health metrics regularly.",
     ["page object", "fixtures", "flaky", "smoke"], ["duplicate selectors in every test"]),
    ("qa-023", "api", "easy", "What is an HTTP 401 status code typically mean?",
     "HTTP 401 Unauthorized usually means the request lacks valid authentication credentials. The client should authenticate or refresh tokens and retry. It is different from 403 Forbidden, which often means identity is known but not allowed.",
     ["401", "authentication", "credentials"], ["401 always means server crash"]),
    ("qa-024", "api", "medium", "What is contract testing for APIs?",
     "Contract testing verifies that a provider and consumer agree on request/response shapes and semantics, often via schemas or consumer-driven contracts. It catches breaking API changes early without full end-to-end environments for every pair.",
     ["contract", "provider", "consumer", "schema"], ["contract testing only checks UI pixels"]),
    ("qa-025", "api", "medium", "How would you test API idempotency for a payment or create endpoint?",
     "Send the same request twice with the same idempotency key or payload and assert only one resource is created and responses are consistent. Verify retries after timeouts do not double-charge. Check status codes and body identity or conflict handling as designed.",
     ["idempotency", "retry", "duplicate", "same request"], ["ignore double-submit behaviour"]),
    ("qa-026", "api", "hard", "What security checks belong in basic API regression?",
     "Include authn/authz failures, injection-like inputs, oversized payloads, sensitive data leakage in errors, HTTPS expectations, and rate limiting if specified. Assert no stack traces or secrets in responses. Pair automated checks with periodic deeper security reviews.",
     ["authorization", "injection", "sensitive data", "error responses"], ["security is only a pen-test once a year and never in QA"]),
    ("qa-027", "process", "easy", "What is a test plan versus a test case?",
     "A test plan describes scope, approach, resources, schedule, and risks for a release or project. A test case is a specific set of steps, data, and expected results for one behaviour. Plans guide strategy; cases execute checks.",
     ["test plan", "scope", "test case", "expected results"], ["plan and case are the same document"]),
    ("qa-028", "process", "medium", "How should QA write a high-quality bug report?",
     "Include a clear title, environment, steps to reproduce, expected versus actual results, severity, evidence (logs/screenshots), and any workarounds. Note build version and whether the issue is new or regressed. Good reports reduce back-and-forth and speed fixes.",
     ["steps to reproduce", "expected", "actual", "evidence"], ["title only is enough for a bug"]),
    ("qa-029", "process", "medium", "What is shift-left testing?",
     "Shift-left moves testing earlier: reviews, unit tests, API checks, and static analysis during development instead of only after a full build. It finds defects when they are cheaper to fix and improves shared ownership of quality.",
     ["earlier", "development", "cheaper", "quality"], ["shift-left means no testing before release"]),
    ("qa-030", "process", "hard", "How do you handle a release when critical bugs remain open?",
     "Communicate residual risk clearly with severity, user impact, and likelihood. Agree go/no-go with product and engineering using documented criteria. Consider feature flags, hotfixes, or delayed rollout. Never hide known critical issues; record the decision and follow-up.",
     ["residual risk", "go/no-go", "impact", "stakeholders"], ["ship silently without mentioning known critical bugs"]),
    ("qa-031", "tooling", "easy", "What is the role of a test management tool like Azure Test Plans or TestRail?",
     "Test management tools organize cases, plans, runs, and traceability to requirements. They track execution status, ownership, and defects linked to cases. They complement automation rather than replacing it.",
     ["test cases", "execution", "traceability"], ["automation makes test management tools useless"]),
    ("qa-032", "tooling", "medium", "When would you choose Pytest over a pure UI recorder tool?",
     "Pytest suits API, unit, and structured automation with fixtures, parametrization, and CI plugins. Recorders can bootstrap UI flows but often produce brittle scripts. Prefer code-first frameworks for maintainable suites and complex assertions.",
     ["fixtures", "parametrization", "maintainable", "CI"], ["recorders are always better than code"]),
    ("qa-033", "tooling", "medium", "What is the benefit of structured logging in test automation?",
     "Structured logs with timestamps, case ids, and step markers speed debugging in CI. They help correlate failures with environment issues and support aggregation. Pair logs with screenshots and traces for UI failures.",
     ["logs", "debugging", "CI", "correlate"], ["print random text without context"]),
    ("qa-034", "concepts", "medium", "What is exploratory testing?",
     "Exploratory testing is simultaneous learning, test design, and execution guided by charters rather than fully scripted steps. It finds unexpected issues automation misses. Sessions should still capture notes, bugs, and coverage ideas.",
     ["exploratory", "learning", "charter", "unscripted"], ["exploratory means random clicking with no notes"]),
    ("qa-035", "concepts", "hard", "What is non-functional testing? Give examples relevant to web APIs.",
     "Non-functional testing checks how a system behaves, not only what it does: performance, reliability, security, usability, and compatibility. For APIs, examples include load/latency, rate limits, availability, and auth hardening under stress.",
     ["non-functional", "performance", "security", "latency"], ["non-functional only means UI colours"]),
    ("qa-036", "strategy", "hard", "How would you test an A/B experiment on a checkout page?",
     "Verify assignment logic, both variants render correctly, metrics events fire, and no PII leaks. Test edge cases like refresh, back button, and logged-out users. Coordinate with analytics owners on success metrics and stop conditions if a variant breaks conversion.",
     ["variants", "assignment", "metrics", "checkout"], ["test only the control variant"]),
    ("qa-037", "api", "easy", "What does JSON schema validation catch in API tests?",
     "JSON schema validation checks types, required fields, enums, and structure of responses. It fails fast when the contract drifts even if status codes stay 200. It does not fully prove business correctness of values.",
     ["schema", "types", "required fields", "contract"], ["schema validation proves all business rules"]),
    ("qa-038", "automation", "medium", "What is test data management and why does it matter?",
     "Test data management is planning creation, isolation, privacy, and cleanup of data used by tests. Poor data causes flakes, false failures, and environment pollution. Prefer fixtures, factories, and dedicated accounts over sharing mutable production-like data blindly.",
     ["test data", "isolation", "cleanup", "flaky"], ["always use production customer data in tests"]),
    ("qa-039", "strategy", "easy", "What is a definition of done for a user story from a QA perspective?",
     "Definition of done should include agreed tests executed, acceptance criteria met, defects of agreed severity resolved or waived, and automation updated when required. It makes quality expectations explicit before a story is called complete.",
     ["acceptance criteria", "tests", "done", "quality"], ["done means code compiled only"]),
    ("qa-040", "concepts", "medium", "What is mutation testing at a high level?",
     "Mutation testing introduces small code changes (mutants) and checks whether the test suite fails them. If mutants survive, tests may be weak. It measures suite effectiveness beyond line coverage, at higher compute cost.",
     ["mutants", "test suite", "effectiveness", "coverage"], ["mutation testing only counts UI clicks"]),
    ("qa-041", "process", "medium", "How can QA support continuous delivery?",
     "Invest in reliable automation, fast smoke suites, test environments that match production contracts, and clear quality signals in the pipeline. Pair with feature flags and progressive delivery. Focus exploratory effort on high-risk changes each release train.",
     ["automation", "pipeline", "smoke", "feature flags"], ["block every deploy for week-long manual only cycles"]),
    ("qa-042", "concepts", "hard", "What is faithfulness in LLM evaluation, and why do QA teams care?",
     "Faithfulness measures whether a model answer stays consistent with provided context instead of inventing facts. QA cares because hallucinations create silent product failures that classical asserts miss. Faithfulness metrics plus golden sets support release gates for RAG and LLM features.",
     ["faithfulness", "context", "hallucination", "golden"], ["faithfulness means the UI looks pretty"]),
]


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    existing = {c["id"] for c in data["cases"]}
    added = 0
    for row in EXTRA:
        cid, cat, diff, q, ans, must, must_not = row
        if cid in existing:
            continue
        data["cases"].append(
            {
                "id": cid,
                "domain": "software_testing_assistant",
                "category": cat,
                "difficulty": diff,
                "question": q,
                "reference_answer": ans,
                "must_include": must,
                "must_not_include": must_not,
                "context": None,
                "tags": [cat, "m4"],
                "source": "M4 golden set expansion",
                "notes": None,
            }
        )
        added += 1
    data["version"] = "1.1"
    data["description"] = (
        f"Golden set for software testing assistant: {len(data['cases'])} cases "
        "(M4 expansion; M1 started with 10 seeds)."
    )
    PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"cases={len(data['cases'])} added={added}")


if __name__ == "__main__":
    main()
