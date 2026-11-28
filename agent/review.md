# Review: accept or reject a match

Run by the orchestrator on every change before it's committed. The orchestrator runs on Opus
and does the review itself; it never hands review to a worker. A byte match is necessary
but not enough: the code also has to be something a person would have written, and something
a port can build on.

## Mechanical checks (all must pass)

1. `python3 tools/agent/lint.py --base HEAD` reports no errors.
2. Built objects for the touched files deleted, then `make verify-<binary>` reports `Match`.
3. Warning count for each touched file is no higher than before (AGENTS.md, "Compiler warnings").
4. `git diff --stat` touches only the source file, its header, the Makefile `EFFECTS` list if
   needed, and `agent/state.json`. Other files are allowed only when the match needs them
   (a shared struct field, a callee's prototype in its owner's header); check each one.
5. If the change touches a header that the effect overlays include (`include/battle.h`,
   `include/effect.h`, `include/battle/*.h`, `include/effect/lib/*.h`, `include/common.h`),
   split every effect overlay and build them all before committing:
   `make split EFFECTS=all && make verify EFFECTS=all`.
   Every binary must report Match. This takes about ten minutes.

## Judgement (read the diff)

Reject, and send back to the worker with the reason, when you see:

- Casts, temporaries, or statement order that only make sense as a way to move bytes, in a
  function that isn't close to the compiler's natural output for simple code.
- Raw offsets on pointers where a struct field belongs. Add or extend the struct instead,
  following CONTRIBUTING.md (one struct type per global; `func_XXXXXXXX_arg0` for a local view).
- Hardware access that isn't behind an SDK call or macro (`include/psxsdk/`). A port will
  replace the SDK, so the game code must not touch hardware directly.
- Names other than locals that aren't the existing placeholders.
- `volatile`, `goto` chains, or empty `do {} while (0)` without an obvious reason.
- A countdown loop without a comment saying the direction is needed for the match.
- Comments that repeat the code, note match status, or say where a value is used.
- Any new documentation: Doxygen blocks, `@brief`, comments on prototypes.
- Invented names for struct fields, union members, flags or parameters. Placeholders keep the
  offset visible (`unk1A`). Union members may name the shape of the data (`word`, `sv`).
- Private structs placed next to the function instead of at the top of the file.
- `void *` or `s32` in a new prototype where the callee's asm shows a struct or pointer type.

Lint warnings are prompts for this read, not automatic rejections.

## Fixing instead of sending back

When the only problems are ones you can fix in a few lines without changing what the code
does (deleting a comment, moving a struct to the top of the file, renaming a field to its
placeholder, giving a prototype its real type), fix them yourself, check the match again, and
count it as a rejection in the run log with what you fixed. Send the work back to the worker
only when the fix needs another round of matching.

## NON_MATCHING candidates

Accept a `NON_MATCHING` block only if all of these hold:

- The worker reported `complete_c: yes` after its full budget plus one round with a hint.
- You've read the C against the asm and believe it behaves the same: same calls with the same
  arguments, same stores, same control flow, same return value.
- It compiles with `make verify-<binary> NON_MATCHING=1` (the build will mismatch; it must
  compile and link).
- The normal build still matches, because the `#else` keeps the `INCLUDE_ASM`.

Record it as `nonmatching` in the state so a later run can try to turn it into a real match.
