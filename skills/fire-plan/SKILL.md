---
name: fire-plan
description: |
  Runs a disciplined, single-session agentic workflow: deep research → 2-3 written proposals → human picks one → plan mode fills the todo list → failing tests → implementation → tests pass → stopwatch benchmarks. Never writes code before the human approves a plan. Trigger phrases: "/fire-plan", "fire plan", "let's fire-plan this", "use fire-plan for", "fire-plan: [task]".
---

# fire-plan

A cost-effective, single-session agentic workflow. The core rule: **no code is written until the human has approved a written plan.**

Overall, prefer tool calls over shell commands. No git commits. Plain text output only.

> All references to `research.md` and `plan.md` mean files inside the run directory `docs/fire-plan/{slug}/` created at the start of Phase 1.

---

## Phase 1 — Research (Ask Mode)

Stay in ask mode. Do not write any code or propose solutions yet.

1. Derive a short kebab-case slug from the task description (e.g. `add-pagination`, `fix-scheduler`, `auth-rewrite`).
2. Create `docs/fire-plan/{slug}/` — this directory is used for all artifacts in this run.
3. Create a task for each phase using `TaskCreate`: Phase 1 Research, Phase 2 Propose, Phase 3 Plan, Phase 4 Tests, Phase 5 Implement, Phase 6 Verify, Phase 7 Audit, Phase 8 Benchmarks, Phase 9 Wrap-up. Mark Phase 1 as `in_progress`.
4. Deep-read all files relevant to the task using `Glob`/`Grep` for discovery, `Read` for deep reading, and `Agent` (subagent_type `Explore`) for broad codebase searches. Skim is not acceptable. If the task involves external libraries or APIs, use the `search-docs` skill (which uses `WebSearch`/`WebFetch` internally) to look up authoritative documentation before forming conclusions.
5. Write findings to `docs/fire-plan/{slug}/research.md`. The file must include:
   - What the affected system does and how it works
   - All relevant files and their responsibilities
   - Existing patterns, conventions, and constraints
   - Potential gotchas or integration risks
6. Mark the Phase 1 task as `completed` via `TaskUpdate`.
7. **Stop and tell the user:** "Research complete. Review `docs/fire-plan/{slug}/research.md` and reply to continue."
8. Wait for explicit user confirmation before proceeding.

---

## Phase 2 — Propose (Ask Mode)

Stay in ask mode. Do not write any code.

1. Mark the Phase 2 task as `in_progress` via `TaskUpdate`.
2. Generate **2–3 distinct approaches** and write them to `docs/fire-plan/{slug}/plan.md`. Each approach must include:
   - A short title and one-sentence summary
   - Key implementation steps (bullet points)
   - Pros and cons
   - Rough complexity (Low / Medium / High)
3. End the file with a blank `## Decision` section for the human to fill in.
4. Mark the Phase 2 task as `completed` via `TaskUpdate`.

**Stop and tell the user:** "Here are your options in `docs/fire-plan/{slug}/plan.md`. Pick one (or add inline notes) and reply with your choice."

> The user may annotate `plan.md` directly — corrections, constraints, rejected sections. If they do, re-read the file, address all notes, update the plan, and ask again. Repeat up to 3 times. Always include `"don't implement yet"` in your own internal guard.

---

## Phase 3 — Plan Mode (After Human Approves)

Once the human has chosen an approach:

1. Mark the Phase 3 task as `in_progress` via `TaskUpdate`.
2. Call `EnterPlanMode` to expand the chosen approach into a full implementation plan inside `plan.md`. When planning is complete, call `ExitPlanMode`. The plan must include:
   - Acceptance criteria (what "done" looks like)
   - Ordered implementation steps
   - Files to create or modify
   - A granular `## Todo` checklist (each item is one atomic task)
   - Performance criteria (if measurable — skip section if not applicable)
3. For each item in the `## Todo` checklist, create a child task under the Phase 5 Implement task using `TaskCreate`.
4. Mark the Phase 3 task as `completed` via `TaskUpdate`.
5. Present the plan to the human for a final review before moving on.

---

## Phase 4 — Tests First

1. Mark the Phase 4 task as `in_progress` via `TaskUpdate`.

Write failing tests **before any implementation code**. Do not make them pass yet.

- Unit tests: one per logical unit of behaviour
- Integration tests: at least one covering the happy path end-to-end
- Name test files clearly so they are easy to find later
- Run the test suite and confirm all new tests **fail** for the right reason
- Append test file paths to the `## Todo` checklist in `plan.md` and create corresponding child tasks via `TaskCreate`

2. Mark the Phase 4 task as `completed` via `TaskUpdate`.

---

## Phase 5 — Implement

1. Mark the Phase 5 task as `in_progress` via `TaskUpdate`.

Issue this prompt to yourself (adapt language to the stack):

> "Implement everything in the todo list. Mark each task as completed both in `plan.md` and via `TaskUpdate` as you finish it. Do not stop until all tasks are checked. Do not add unnecessary comments or docs. Continuously use the `LSP` tool for type-checking diagnostics and run the linter to catch issues early."

Rules during implementation:
- Follow the plan exactly; do not invent scope
- When completing each todo item: mark it `[x]` in `plan.md` **and** call `TaskUpdate` to mark the corresponding task `completed`
- If a task is blocked, note it inline in `plan.md` and continue with the next task
- Run the full test suite after each logical group of tasks, not only at the end

2. Once all todo items are done, mark the Phase 5 task as `completed` via `TaskUpdate`.

---

## Phase 6 — Verify Tests Pass

1. Mark the Phase 6 task as `in_progress` via `TaskUpdate`.

Run the full test suite. All tests (old and new) must be green before continuing.

If a test fails:
1. Read the failure output carefully
2. Fix the implementation (not the test) unless the test itself was wrong
3. Re-run until clean
4. Do not comment out or skip tests to make the suite pass

2. Mark the Phase 6 task as `completed` via `TaskUpdate`.

---

## Phase 7 — Code Audit

Skip this phase (and mark its task `completed`) if no modified files are Python or C#.

1. Mark the Phase 7 task as `in_progress` via `TaskUpdate`.
2. Run the `code-audit` skill against modified files only (not the whole repo). Review the findings with the human and address any violations before moving on. Do not silently ignore findings — note any deferred items in `plan.md` under `## Audit Notes`.
3. Mark the Phase 7 task as `completed` via `TaskUpdate`.

---

## Phase 8 — Stopwatch Benchmarks

Skip this phase (and mark its task `completed`) only if the plan's performance criteria section is marked "N/A".

1. Mark the Phase 8 task as `in_progress` via `TaskUpdate`.
2. Write inline stopwatch benchmarks — no external benchmarking library required. See [references/benchmarks.md](references/benchmarks.md) for language-specific stopwatch patterns.
3. Compare results against the performance criteria in `plan.md`. If a threshold is not met, note it in `plan.md` under `## Performance Results` and surface it to the human — do not silently skip.
4. Mark the Phase 8 task as `completed` via `TaskUpdate`.

---

## Phase 9 — Wrap-up

1. Mark the Phase 9 task as `in_progress` via `TaskUpdate`.
2. Mark the plan status at the top of `plan.md`: `**Status: DONE ✓**`
3. Append a brief `## Lessons` section to `plan.md` with anything non-obvious learned during implementation
4. Mark the Phase 9 task as `completed` via `TaskUpdate`.
5. Print a short summary to the human: what was built, test results, benchmark results (if run), any open items

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Tests pass before any implementation | The tests are testing the wrong thing — re-read them and fix assertions |
| Plan mode produces a generic plan | Add more detail to `research.md` and re-run Phase 2 before entering plan mode |
| Implementation drifts from the plan | Stop, revert with `git checkout .`, narrow scope in `plan.md`, restart Phase 5 |
| Context window fills up mid-session | Point Claude back to `plan.md` and `research.md` — they survive compaction |
| Benchmark is slower than threshold | Do not tune blindly — profile first, identify the bottleneck, propose a fix to the human |

---

## Examples

**Example 1 — New feature**
> User: `/fire-plan add keyset pagination to the /posts endpoint`
> Claude: Reads the posts controller, ORM layer, and existing pagination. Writes `research.md`. Waits. Then writes 3 approaches to `plan.md` (offset, keyset, hybrid). Waits for human to pick. Enters plan mode. Writes failing tests. Implements. Runs tests. Benchmarks query time vs. the 50ms threshold in the plan.

**Example 2 — Bug fix**
> User: `fire-plan: the task scheduler is running cancelled tasks`
> Claude: Traces the scheduler, cancellation flow, and queue consumer. Writes `research.md` documenting where cancellation state is checked (and missed). Proposes 2 fixes. Waits. Implements the chosen fix behind a failing regression test first.

**Example 3 — Refactor**
> User: `let's fire-plan the auth middleware rewrite`
> Claude: Deep-reads all middleware, session handling, and callers. Writes `research.md`. Proposes 2 approaches (drop-in replacement vs. incremental migration). Human annotates plan.md with "no breaking API changes". Claude updates plan, enters plan mode, writes tests that assert existing API contracts, then implements.
