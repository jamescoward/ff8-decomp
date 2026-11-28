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
2. `./permute.sh --asm-dir <folder> <name>`. Always pass the folder: overlays share function
   names. The script finds the source file and reads the compiler settings from the Makefile.
3. Edit `permuter/<name>/base.c`, run `./permuter/<name>/diff.sh`, repeat.
4. Get the structure right first (control flow, calls, types). Only reach for statement order,
   temporaries or register tricks when the diff is a handful of instructions.

## What a match is not allowed to contain

Raw addresses or offsets, inline asm, register pinning, casts that only exist to move bytes,
an `extern` inside a function, invented names for anything other than locals. If the only way
to match needs one of these, stop and report it; the orchestrator decides.

Review sends work back for these more than anything else, so get them right first time:

- Struct fields, union members you add, flags and parameters get placeholders that keep the
  offset or value visible (`unk1A`, `FUNC_800C8E54_FLAG_8000`), never names that say what you
  think they mean (`mode`, `slot`, `id`). Union members may name the shape of the data
  (`word`, `half`, `sv`), as existing code does.
- Private typedefs and structs go at the top of the .c file, after the includes and existing
  prototypes, never next to the function. Field offsets go in front: `/** 0x0E */ s16 unkE;`.
- A prototype gets the types the callee really uses: read the callee's asm. Never `void *` or
  `s32` as a shortcut for a pointer. Use an existing struct (`BattleEffectSlot`, `EffectEntity`)
  when its layout fits; when it doesn't, make a view named after the function.
- Don't add documentation of any kind: no Doxygen, no `@brief`, no comments on new prototypes.
  A comment is only for something the code can't say, such as a cast the match needs.
- Keep the diff to the function, its own file and its own header. Change a shared header
  (`battle.h`, `effect.h`, or anything every effect overlay includes) only when the match
  can't be written without it, and say so in the report.
- Single-bit flags get placeholder `#define`s. Compare pointers against `NULL`.

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
files: <every file you changed>
shared_headers: yes | no   (did you change a header every effect overlay includes?)
warnings: <file> <before> -> <after>, for each file you changed
```
