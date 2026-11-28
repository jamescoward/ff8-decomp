# Orchestrator: one scheduled run

You run unattended, on Opus. Nobody will answer questions, so never stop to ask one: when
something is unclear, decide, write the decision in the run log, and carry on. Work through
the steps, record what happened, push, and stop. Read AGENTS.md (the fork rules at the top
come first), CONTRIBUTING.md, `agent/worker.md` and `agent/review.md` before you start.

You are the reviewer for every match. Workers match; you judge.

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

Do up to **8 functions** this run (fewer if the session is running long). `pick.py next`
already leaves out functions whose asm doesn't look like a whole function
(`pick.py suspects` lists them); don't hand those to a worker. For each:

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
3. Start the worker with the Agent tool (that model, `run_in_background: false`). Give it
   the picked JSON, the budget, any previous notes, and tell it to follow `agent/worker.md`,
   including its list of what review rejects. Wait for its report before doing anything else.
4. If the worker reports `stuck` with `best_diff` of 20 or less: read the target asm and the
   worker's `permuter/<name>/base.c` and diff yourself, write a concrete hint (which construct
   the compiler wants, what to change), and run one more worker round with `sonnet` and the
   hint. If the diff is 3 or less after that, you may let it run
   `timeout 600 ./permute.sh --run -j2 --asm-dir <folder> <name>` once.
5. On `matched`: review the change by `agent/review.md`. Fix small problems yourself as it
   describes. If it needs another round of matching, send it back to the worker once with
   the reason; if it fails again, revert `src/` and `include/` and treat it as stuck. If it
   passes, commit it (see Committing).
6. On `stuck` or `blocked`: if `agent/review.md` allows a NON_MATCHING block, add it, check it,
   and commit it. Otherwise make sure `src/` is unchanged (`git checkout -- src include Makefile`).
7. Record the result:
   `python3 tools/agent/pick.py record <key> --status <matched|nonmatching|stuck|skipped> --model <m> --attempts 1 --best <n> --note "<where_stuck or purpose>"`.
   Use `skipped` for functions that need something the loop can't do (a config or splat
   change, a struct that touches many files). Say why in the note.
8. Add a row to the run log, `agent/pilot.md` (create it with the header row if it's
   missing):
   `| date | key | tier | size | model(s) | diff runs | hint given | best diff | result | review rejections | lint errors | notes |`.
   `result` is matched, nonmatching, stuck, blocked or skipped. `review rejections` counts
   every time review found a problem, whether you fixed it or sent it back, and `notes` says
   what it was. When it didn't match, `notes` says in a sentence what made it hard.

One function at a time. Never two workers at once.

## 4. Finish

1. `make full`. If it fails, find the commit from this run that broke it, revert it, record
   that function as `stuck` with the reason, and run `make full` again.
2. Add a "Run summary" section under the run log table for this run, below earlier runs'
   summaries: matches per model, match rate by size band (under 0x100, 0x100-0x300,
   larger), how often Haiku failed where Sonnet then succeeded, and the most common reasons
   for review rejections. Commit `agent/state.json` and `agent/pilot.md` together
   ("Update agent state").
3. `git -c push.negotiate=true push -u origin agent-work`.
4. Open a pull request from `agent-work` to `main`, titled "Agent work <date>", not as a
   draft. Use the GitHub tools the session has (the GitHub MCP pull request tools, or
   `gh api repos/{owner}/{repo}/pulls`; GraphQL-based `gh pr` commands may be blocked).
   If one is still open from an earlier run (its merge failed), add this run's section to its
   body instead. A person reads it afterwards without being a C expert, so for each function
   the body says in plain English:
   - what it seems to do (no name suggestions),
   - anything unusual about the C: a cast or odd construct the match needs, a new struct
     view, a shared header it changed,
   - what review found and fixed or let through, and why.
   Then list NON_MATCHING blocks, and skipped or stuck functions with the reason.
5. Merge the pull request into `main` with the merge method `merge`, so each function keeps
   its own commit, and pass the SHA you pushed as the expected head. Merge only when
   `make full` passed in step 1 on exactly what you pushed and every change in it went
   through review. If this run committed nothing but `agent/state.json` and `agent/pilot.md`,
   merge it all the same. If the merge fails (a conflict, or `main` moved), leave the pull
   request open and say so in the reply; the next run merges `main` in and tries again.
6. Reply with a short summary: functions tried, matched, NON_MATCHING, stuck, skipped, which
   worker model got each, and anything a person needs to look at.

## Committing

- One commit per function, staged by name (never `git add -A`).
- Subject in the imperative, e.g. "Decompile func_800B49D8 in bc_object10". For a
  NON_MATCHING block: "Add NON_MATCHING C for func_800B49D8".
- No match statuses in the message, no AI attribution lines, as AGENTS.md says.
- Never commit anything under `rom/`, `original/`, `asm/`, `build/`, `expected/` or `permuter/`.
- Never push to `main`: changes reach it only by merging the pull request in Finish. Never
  force-push or rewrite history that's already pushed.
- Never commit `emu/` or a memory card or savestate.
