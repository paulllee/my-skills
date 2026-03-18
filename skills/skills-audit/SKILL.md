---
name: skills-audit
description: |
  Audits all skills in the skills/ directory against quality best practices: structural integrity, YAML frontmatter correctness, instructional quality, and design patterns. Reports violations per pillar with suggested fixes. Does NOT auto-fix — surfaces issues for the human to review. Trigger phrases: "/skills-audit", "audit my skills", "check my skill quality", "run a skills audit".
---

# skills-audit

A read-only audit of every skill in `skills/` against authoring best practices. No changes are made — violations and suggested corrections are reported so the human can decide what to fix.

---

## How to Run

- `/skills-audit` — audit all skills under `skills/`
- `/skills-audit code-audit` — audit a single skill by folder name

---

## Step 1 — Discover Skills

Use `Glob` to find all `skills/*/SKILL.md` files. Print the count before proceeding:

> "Found 4 skills. Auditing now…"

---

## Step 2 — Audit Each Skill

For each `SKILL.md`, read it and evaluate all four pillars below.

### Pillar 1 — Structural Integrity

| Check | What to look for |
|---|---|
| File named `SKILL.md` | Any other casing or name fails |
| Folder is `kebab-case` | No spaces, underscores, or capital letters in the folder name |
| No `README.md` inside the skill folder | All docs must live in `SKILL.md` or a `references/` subdirectory |

### Pillar 2 — YAML Frontmatter

| Check | What to look for |
|---|---|
| Enclosed by `---` delimiters | Missing opening or closing `---` |
| Description under 1024 characters | Count characters in the `description` field |
| Description states WHAT and WHEN | Must describe what the skill does and include trigger phrases |
| No XML angle brackets in frontmatter | `<` or `>` characters in any frontmatter field |

### Pillar 3 — Instructional Quality

| Check | What to look for |
|---|---|
| Progressive disclosure | Lengthy API specs or reference docs should be in `references/`, not inline |
| Actionable steps | Vague advice ("handle errors") without specific commands or tool calls |
| Troubleshooting section | Missing a table or section with common failures and fixes |
| 2–3 concrete examples | Fewer than 2 trigger/action examples, or examples that are too abstract |

### Pillar 4 — Design Pattern

Identify which pattern the skill uses and confirm it is implemented correctly:

| Pattern | Signals |
|---|---|
| **Sequential Orchestration** | Numbered steps with clear validation gates between them |
| **Iterative Refinement** | A loop that improves output until a quality threshold is met |
| **Multi-MCP Coordination** | Explicit data flow between two or more distinct tools/MCPs |

Flag skills that implement no recognizable pattern or mix patterns incoherently.

---

## Step 3 — Report

Output one section per skill, grouped by pillar. Use this format:

```
## skills-audit Results

### code-audit

#### Pillar 1 — Structural Integrity
[PASS] Folder is kebab-case, file is named SKILL.md, no README present.

#### Pillar 2 — YAML Frontmatter
[IMPROVE] Description does not explicitly list trigger phrases.
> Suggested fix: add `Trigger phrases: "/code-audit", "audit my code"` to the description field.

#### Pillar 3 — Instructional Quality
[PASS] Troubleshooting table present, 3 examples provided, steps are actionable.

#### Pillar 4 — Design Pattern
[PASS] Sequential Orchestration — clear numbered steps with a final report gate.

---

### fire-plan
...
```

If a skill passes all pillars, output a single `[PASS] All pillars pass.` line for it.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `skills/` directory not found | Confirm the working directory is the skills repo root; ask the user to confirm the path |
| Frontmatter character count unclear | Count only the `description` value, excluding the `description:` key and `\|` block indicator |
| Skill uses a pattern not listed | Note it as an observation under Pillar 4, don't force-fit it to an existing pattern |

---

## Examples

**Example 1 — Full audit**
User: `/skills-audit`
Claude: Globs all `skills/*/SKILL.md`, audits each against all four pillars, prints a grouped violation report.

**Example 2 — Single skill**
User: `/skills-audit fire-plan`
Claude: Reads only `skills/fire-plan/SKILL.md`, reports pass/fail per pillar.
