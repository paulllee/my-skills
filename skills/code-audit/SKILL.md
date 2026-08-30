---
name: code-audit
description: check files for simple english, small tests, and clear code
---

## scope

check changed files unless the user gives another scope. check all text and code. read repo rules first. do not edit unless the user or map asks for fixes

## writing

use plain text, simple words, and the fewest words that keep the meaning clear. reply in the language the user uses. use lowercase for prose and allow capitals only when a literal name, code value, or language requires them

do not end a prose source line with a period. use short useful headings when they make a file easier to scan. flag headings that repeat the text or split related content too often. avoid tables, dividers, long lists, hard wraps, and extra detail unless the user or file format needs them. use one source line for each paragraph and list item

use backticks only for code, names, paths, and flags. use a code block when inline code is hard to read. use plain ascii unless other text needs more

## code

flag unclear names, repeated work, extra layers, hidden flow, and work outside scope. prefer no comments or docstrings. allow one short comment when it says why or one short docstring when it adds needed facts

require braces for each control flow body in a language with braces. do not allow a braceless one-line control flow

## tests

keep tests tiny and flat. make each test name say what it proves. flag arrange-act-assert parts and test comments. test each behavior once unless another test finds a different risk

## c#

use XML docs only when a public API needs them. allow a plain `summary` with no refs when that is enough. flag XML docs that only repeat the name or type

## report

put sure issues before unsure issues. give the file and line, rule, proof, and smallest fix for each issue. if there are no issues, say so in one short line
