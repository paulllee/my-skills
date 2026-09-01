---
name: map
description: plan coding work with choices, tests, checks, and human review. use when the user asks to map a task
---

## files

keep each map in `~/.maps/{project}/{slug}`. use the repo name for `project` and a short kebab-case task name for `slug`. keep all plans, notes, checks, and handoff files there. do not commit or push unless the user asks

## start

ask if the user wants a new git worktree. write the task, repo, branch, worktree choice, state, and short phase list to `run.md`. wait to make the worktree until coding starts

## research

read the code, tests, settings, repo rules, useful past maps, and official docs when current behavior matters. write only useful facts, files, rules, risks, and past lessons to `research.md`. do not pick a fix yet

## choices

write two or three real choices to `proposals.json` in the map folder. the schema is in the docstring at the top of [scripts/pages.py](scripts/pages.py). read only the docstring (about the first 60 lines), never the rest of the file. for each choice, put the idea in `summary`, key changes in `steps`, good parts in `pros`, bad parts and risks in `cons`, and rough size in `complexity`. say which choice you prefer and why in the `description` field. keep the `task` field short, it is the page title

show the choices on a page. run in the background:

    pixi exec python <this skill's folder>/scripts/pages.py proposals <map folder>

the page opens in the browser and the script exits when the user hits send. read `feedback.json`. if there are comments, answer each one in the `replies` field of `proposals.json`, update the choices, and rerun the script. do not code before a choice is picked

## plan and delegation

after approval, use plan mode if the app has it. write the scope, done checks, files, work order, and risks to `plan.md`. ask again only if this changes the approved choice in a real way

for each new user request during the map, first check if it is bounded and can run alone. if it can, give it to a subagent to keep the main context small. for implementation, wait until any needed failing tests exist

do not let agents edit the same files at the same time. keep choices, approvals, user questions, shared files, integration, and tightly linked work with the main agent

## tests

make or enter the worktree now if the user chose one. add the fewest tests that prove the new behavior. run each new test before coding and check that it fails because the behavior is missing

write the command and useful failure in `run.md`. if the test passes, fix it before coding

## implementation and checks

code only the approved work. follow repo rules and useful local patterns. run small checks while coding, then run the right tests, lint, format, type, and build checks

write the commands and results to `validation.md`. do not hide, skip, or weaken a failure

## audit and review

give the changed files and repo rules to a fresh subagent. have it run `code-audit` and report findings without editing. fix clear issues that are in scope and write any kept issue and its reason to `audit.md`

make the diff with git itself. a shell `>` redirect can re-encode and mangle unicode:

    git diff --output=<map folder>/diff.patch

append a plain english note of what was built or changed this round to `summary.json`, a json list of strings, one entry per round. the page shows it as a thread at the top and numbers the rounds itself, so no round prefixes in the text. then run in the background with the repo as the working folder so the page can show unchanged lines:

    pixi exec python <this skill's folder>/scripts/pages.py review <map folder>

read `review-feedback.json`. treat each comment as the next work request in the approved scope, or push back by answering it in `replies.json`. for a behavior change, change or add a test and check its failure first. code, check, audit, remake the diff, add to `summary.json`, and rerun the script until approved

## finish

write the final state, checks, worktree path, and open work to `run.md`. tell the user what changed and how to use the worktree if needed

never run git commit or git push
