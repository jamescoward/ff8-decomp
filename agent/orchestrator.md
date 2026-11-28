# Orchestrator: one scheduled run

You run unattended. Nobody will answer questions. Work through the steps, record what
happened, push, and stop. Read AGENTS.md (the fork rules at the top come first),
CONTRIBUTING.md, `agent/worker.md` and `agent/review.md` before you start.

## 1. Get on the work branch

```
git fetch origin main agent-work || git fetch origin main
git checkout agent-work 2>/dev/null || git checkout -b agent-work origin/main
git merge --no-edit origin/main
```

If the merge conflicts, abort it, push nothing, report the conflict, and stop.

## 2. Check the baseline

If `asm/` or `build/` is missing, the setup script didn't run: run
`bash tools/agent/setup-cloud.sh`. Setup splits from `main`, so `agent-work` may list effect
overlays in `EFFECTS` that have no asm yet. Split those:

```
for o in $(sed -n 's/^EFFECTS ?= //p' Makefile); do [ -d asm/ovl/$o ] || make split-$o; done
```

Then `make verify`. If the baseline doesn't match, report
which binaries mismatch and stop. Never start from a broken build.

## 3. Work through functions

Do up to **5 functions** this run (fewer if the session is running long). For each:

1. `python3 tools/agent/pick.py next` gives the function. If it says `"needs_split": true`,
   its effect overlay isn't split yet: add the binary to `EFFECTS` in the Makefile, run
   `make split-<binary>` and `make verify-<binary>`. If that matches, commit the Makefile
   ("Build <binary> by default") and run `pick.py next` again for the function and its size.
   If it doesn't, revert the Makefile, record the function as `skipped` with the reason, and
   pick again. Then mark the function:
   `python3 tools/agent/pick.py record <key> --status in_progress`.
2. Choose the worker model:
   - `haiku` when the size is 0x100 bytes or less and it has no previous attempts,
   - `sonnet` otherwise, and for any retry.
3. Start the worker with the Agent tool (that model, not in the background). Give it the
   picked JSON, the budget, any previous notes, and tell it to follow `agent/worker.md`.
4. If the worker reports `stuck` with `best_diff` of 20 or less: read the target asm and the
   worker's `permuter/<name>/base.c` and diff yourself, write a concrete hint (which construct
   the compiler wants, what to change), and run one more worker round with `sonnet` and the
   hint. If the diff is 3 or less after that, you may let it run
   `timeout 600 ./permute.sh --run -j2 --asm-dir <folder> <name>` once.
5. On `matched`: review the change by `agent/review.md`. If it fails review, send it back to
   the worker once with the reason; if it fails again, revert `src/` and treat it as stuck.
   If it passes, commit it (see Committing).
6. On `stuck` or `blocked`: if `agent/review.md` allows a NON_MATCHING block, add it, check it,
   and commit it. Otherwise make sure `src/` is unchanged (`git checkout -- src include Makefile`).
7. Record the result:
   `python3 tools/agent/pick.py record <key> --status <matched|nonmatching|stuck|skipped> --model <m> --attempts 1 --best <n> --note "<where_stuck or purpose>"`.
   Use `skipped` for functions that need something the loop can't do (a config or splat
   change, a struct that touches many files). Say why in the note.

One function at a time. Never two workers at once.

## 4. Finish

1. `make full`. If it fails, find the commit from this run that broke it, revert it, record
   that function as `stuck` with the reason, and run `make full` again.
2. Commit `agent/state.json` ("Update agent state").
3. `git -c push.negotiate=true push -u origin agent-work`.
4. If no pull request from `agent-work` to `main` is open
   (`gh api "repos/{owner}/{repo}/pulls?head=jamescoward:agent-work&state=open"`), open a
   draft one titled "Agent work" with
   `gh api repos/{owner}/{repo}/pulls -f title='Agent work' -f head=agent-work -f base=main -f body='...' -F draft=true`
   (GraphQL-based `gh pr` commands may be blocked in cloud sessions). Keep the body to what's in it: matched functions,
   NON_MATCHING blocks, skipped functions and why.
5. Reply with a short summary: functions tried, matched, NON_MATCHING, stuck, skipped, which
   worker model got each, and anything a person needs to look at.

## Committing

- One commit per function, staged by name (never `git add -A`).
- Subject in the imperative, e.g. "Decompile func_800B49D8 in bc_object10". For a
  NON_MATCHING block: "Add NON_MATCHING C for func_800B49D8".
- No match statuses in the message, no AI attribution lines, as AGENTS.md says.
- Never commit anything under `rom/`, `original/`, `asm/`, `build/`, `expected/` or `permuter/`.
- Never push to `main`.
