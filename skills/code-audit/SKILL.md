---
name: code-audit
description: |
  Manually audits Python and/or C# source files against Paul's coding standards. Reports violations grouped by rule with file and line references. Does NOT auto-fix — surfaces issues for the human to review. Trigger phrases: "/code-audit", "audit my code", "check my python standards", "check my csharp standards", "run a code audit", "audit standards".
---

# code-audit

A manual, read-only audit of Python and C# files against author's personal coding standards. No changes are made — violations are reported so the human can decide what to fix.

---

## How to Run

The user may scope the audit in several ways:

- `/code-audit` — audit all `.py` and `.cs` files in the current working directory (recursive)
- `/code-audit src/` — audit a specific folder
- `/code-audit foo.py` — audit a single file
- `/code-audit --python` / `/code-audit --csharp` — restrict to one language

If no scope is given, default to all `.py` and `.cs` files under the current directory, skipping `node_modules/`, `.venv/`, `bin/`, `obj/`, and `.git/`.

---

## Step 1 — Discover Files

Use `Glob` to find all in-scope files. Print the file count before proceeding:

> "Found 12 Python files and 7 C# files. Auditing now…"

---

## Step 2 — Audit Python Files

For each `.py` file, use `Read` to load it and check every rule below. Record each violation with **file path**, **line number**, and a **one-line description**.

### Python Rules

| # | Rule | What to look for |
|---|------|-----------------|
| PY-1 | Type hints on all function signatures | Any `def` missing param types or return type annotation |
| PY-2 | Google-style docstrings on public functions/classes | Public `def` or `class` (not prefixed with `_`) missing a docstring, or docstring not using Google style (`Args:`, `Returns:`, `Raises:`) |
| PY-3 | snake_case for functions and variables | Function names or local variables using camelCase or PascalCase |
| PY-4 | PascalCase for classes | Class names not starting with an uppercase letter |
| PY-5 | Prefer f-strings | `.format(` calls or `%` string formatting that could be an f-string |
| PY-6 | Use pathlib over os.path | `os.path.join`, `os.path.exists`, `os.path.dirname`, etc. |
| PY-7 | Import order: stdlib → third-party → local (blank line between groups) | Imports not grouped correctly or missing blank line separators |
| PY-8 | Variable type hints | Two sub-rules: (1) Always annotate variables whose type cannot be inferred at initial assignment — e.g. `x = []` should be `x: list[str] = []`. (2) Always annotate variables assigned from a function call, even if mypy can infer the return type — e.g. `result: MyType = get_result()` is preferred over `result = get_result()`. Rationale: mypy infers from the static type of the value expression, but explicit annotations at call sites make intent clearer at a glance. |

---

## Step 3 — Audit C# Files

For each `.cs` file, use `Read` to load it and check every rule below.

### C# Rules

| # | Rule | What to look for |
|---|------|-----------------|
| CS-1 | Mandatory braces on all control flow | `if`, `else`, `for`, `foreach`, `while`, or `using` blocks without `{` `}` (single-line braceless statements) |
| CS-2 | PascalCase for public members | Public methods, properties, or fields not in PascalCase |
| CS-3 | _camelCase for private fields | Private fields not prefixed with `_` or not in camelCase after the underscore |
| CS-4 | Nullable reference types enabled | Check `.csproj` files in scope for `<Nullable>enable</Nullable>`; flag any project missing it |
| CS-5 | XML doc comments on public APIs | Public methods or classes missing `/// <summary>` doc comments |
| CS-6 | Prefer pattern matching over type casting | `as` casts followed by null checks, or `(TypeName)expr` casts where pattern matching (`is TypeName x`) could be used |

---

## Step 4 — Report

After auditing all files, output a structured report grouped by rule. Use this format:

```
## Python Audit

### PY-1 — Type hints on all function signatures
- src/utils/parser.py:14  `def parse(data)` — missing param and return types
- src/utils/parser.py:31  `def build_tree(nodes)` — missing return type

### PY-5 — Prefer f-strings
- src/models/user.py:88  `"Hello, {}".format(name)` — convert to f-string

### PY-8 — Variable type hints
- src/utils/parser.py:10  `items = []` — empty container, type not inferrable; annotate as `items: list[str] = []`
- src/utils/parser.py:22  `result = get_result()` — function call result should be explicitly annotated: `result: MyType = get_result()`

---

## C# Audit

### CS-1 — Mandatory braces on all control flow
- Services/OrderService.cs:42  `if (x > 0) return;` — missing braces

### CS-4 — Nullable reference types enabled
- MyProject/MyProject.csproj — <Nullable> not set to enable

---

## Summary
- Python violations: 3 across 2 files
- C# violations: 2 across 2 files
- Files with no violations: 15
```

If a file has zero violations, do **not** list it — only surface issues.

If no violations are found at all, say: "Audit complete. No violations found."

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Too many files to read in one pass | Process directory by directory; report partial results and continue |
| Ambiguous import order (stdlib vs third-party) | Flag it as a note, not a hard violation; ask the human if unsure |
| .csproj not in the scoped path | Note that CS-4 could not be verified and list the projects checked |

---

## Examples

**Example 1 — Full audit**
> User: `/code-audit`
> Claude: Globs all `.py` and `.cs` files, reads each, checks all rules, prints a grouped violation report.

**Example 2 — Scoped to one language**
> User: `/code-audit --python src/`
> Claude: Audits only `.py` files under `src/`, skips C# rules entirely.

**Example 3 — Single file**
> User: `/code-audit Services/PaymentService.cs`
> Claude: Reads that one file, checks C# rules, reports any violations.
