# Worker: match one function

You get one function from the orchestrator: its key, asm folder, name, source file, binary,
size, and any notes or hint from earlier attempts. Your job is to write C that compiles to the
same bytes, and nothing else.

Read AGENTS.md ("Matching one function" and "Review your change") and CONTRIBUTING.md first.
The fork rules at the top of AGENTS.md apply.

## Budget

- At most 30 runs of `diff.sh` (the orchestrator may give a different number).
- Stop early if 8 runs in a row don't lower the diff count. Report stuck.
- Don't run the permuter unless the orchestrator says so.

## Steps

1. `python3 tools/m2c/m2c.py -t mipsel-gcc-c <folder>/<name>.s` for a first draft. Look in the
   same source file for matched neighbours: they show the structs, types and style in use.
   For effect overlays, search the other `src/effect/` files for a function with the same shape;
   many effect overlays share code, and a matched twin is the fastest route.
2. `./permute.sh <name>` (add `--psyq 4.3` if the file is in `PSYQ43_SRCS` in the Makefile).
3. Edit `permuter/<name>/base.c`, run `./permuter/<name>/diff.sh`, repeat.
4. Get the structure right first (control flow, calls, types). Only reach for statement order,
   temporaries or register tricks when the diff is a handful of instructions.

## What a match is not allowed to contain

Raw addresses or offsets, inline asm, register pinning, casts that only exist to move bytes,
an `extern` inside a function, invented names for anything other than locals. If the only way
to match needs one of these, stop and report it; the orchestrator decides.

## When it matches

Move the code into the source file in place of the `INCLUDE_ASM`, with types and prototypes
where CONTRIBUTING.md puts them. Delete the built objects for that file, then run
`make verify-<binary>`. If the binary is an effect overlay not in `EFFECTS` in the Makefile,
add it there first. Don't commit; the orchestrator does.

## When it doesn't

Leave `src/` as it was. If your best C is complete and you believe it does the same thing as
the asm, keep it in `permuter/<name>/base.c` so the orchestrator can consider it for a
`NON_MATCHING` block.

## Report

Reply with exactly this, filled in:

```
key: <key>
result: matched | stuck | blocked
diff_runs: <n>
best_diff: <instructions still different, 0 if matched>
complete_c: yes | no   (does base.c cover the whole function?)
where_stuck: <one or two sentences: which instructions differ and what you tried>
purpose: <one sentence on what the function seems to do; no name suggestions>
```
