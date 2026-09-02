---
name: code-audit
description: check files for simple english, small tests, and clear code
---

## scope

check changed files unless the user gives another scope. when the scope is a folder, skip generated and vendor folders like `node_modules`, `.venv`, `bin`, `obj`, and `.git`. check all text and code. read repo rules first. do not edit unless the user or map asks for fixes

each rule below has an id so a repo rules file can override one by name. house style comes only from a repo rules file like AGENTS.md, never from patterns in old files or commit messages. when a repo rules file conflicts with a rule, report the issue, say it loses to house style, and do not fix it. old files keep their style, but new and moved code follows the rules

## writing

these rules cover prose in any checked file and the audit report itself. reply in the language the user uses

- WR-1 plain text, simple words, and the fewest words that keep the meaning clear
- WR-2 lowercase prose. capitals only when a literal name, code value, or language requires them
- WR-3 no period at the end of a prose source line
- WR-4 short useful headings only. flag headings that repeat the text or split related content too often
- WR-5 no tables, dividers, long lists, hard wraps, or extra detail unless the user or file format needs them. one source line for each paragraph and list item
- WR-6 backticks only around code, names, paths, and flags. use a code block when inline code is hard to read. never backticks on ordinary words for emphasis
- WR-7 plain ascii unless the text needs more. no bold for emphasis
- WR-8 code comments and xml doc summaries are prose: lowercase, fewest words, no trailing period. literal names keep their case

## code

- CO-1 clear names that say what the thing is or does
- CO-2 no repeated work
- CO-3 no extra layers
- CO-4 no hidden flow
- CO-5 no work outside the task's scope
- CO-6 prefer no comments or docstrings. allow one short comment when it says why or one short docstring when it adds needed facts. moved or copied code does not grandfather its comments. a comment that restates what the next lines do is noise wherever it came from
- CO-7 braces for each control flow body in a language with braces. no braceless one-line control flow
- CO-8 write config files bare: no comments in ci yaml, toml, csproj, or other build xml, context goes in the commit message. a json comment key is a comment: allow one only when it states a constraint the format cannot express
- CO-9 keep a statement on one line when it fits in about 120 characters. never wrap mid-statement for style

## python

- PY-1 type hints on every def, params and return
- PY-2 f-strings, never `format(` or `%`
- PY-3 pathlib over os.path
- PY-4 imports grouped stdlib, third party, local, all at module top, never inside a function unless a verified circular import forces it
- PY-5 no time.sleep polling loops. use the client library's own blocking wait or timeout

## c#

- CS-1 xml docs only when a public api needs them. a plain `summary` is enough: never `see cref`, `c`, or `paramref` tags, write names as plain words. flag xml docs that only repeat the name or type
- CS-2 `<Nullable>enable</Nullable>` in every csproj in scope. if none is in scope, say the check could not run and list the projects you saw
- CS-3 pattern matching like `is TypeName x` over `as` plus null check or hard casts
- CS-4 when a config section already binds to an options class, add the property there instead of `configuration["section:key"]` lookups

## tests

- TE-1 keep tests tiny and flat. flag arrange-act-assert parts and test comments
- TE-2 make each test name say what it proves in the fewest words. a description attribute or docstring only for a needed fact the name cannot carry, and it must not restate the name
- TE-3 test each behavior once unless another test finds a different risk. near-duplicate tests that differ only in a literal become one parameterized test
- TE-4 no docstrings in new tests, even when older tests in the file carry them. house style does not grandfather new additions

## report

put sure issues before unsure issues. give the file and line, rule id, proof, and smallest fix for each issue. say how many files you checked and how many were clean. on a huge scope, go folder by folder and report as you go. if there are no issues, say so in one short line
