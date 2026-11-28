# Agent loop pilot

| date | key | tier | size | model(s) | diff runs | hint given | best diff | result | review rejections | lint errors | notes |
|------|-----|------|------|----------|-----------|------------|-----------|--------|-------------------|-------------|-------|
| 2026-11-28 | asm/ovl/battle/nonmatchings/bc_object9/func_800B3534 | 2 battle | 0x40 | haiku | 1 | no | 19 | blocked | 0 | 0 | Compares against `$sp` with no stack frame ($t0/$t1 temps), so it looks like hand-written asm; can't be written in C without inline asm. Recorded as skipped in state.json. |
| 2026-11-28 | asm/ovl/battle/nonmatchings/bc_object10/func_800B49D8 | 2 battle | 0x9c | haiku | 4 | no | 0 | matched | 1 | 0 | Rejected once: private structs placed next to the function instead of at the top of the file, and func_800C5A34 prototyped with `void *` where its asm reads a BattleEffectSlot. Both fixed by the same worker. |
| 2026-11-28 | asm/ovl/battle/nonmatchings/bc_object12/func_800BFF38 | 2 battle | 0x160 | sonnet | 0 | no | - | skipped | 0 | 0 | Split wrong: this is the middle of one function that runs from func_800BFE1C through func_800C0098 (no prologue, uses s1/s2 set earlier). Needs a splat config change to merge the five symbols, which the loop doesn't do. Worker reported blocked. |
| 2026-11-28 | asm/ovl/battle/nonmatchings/bc_object22/func_800E1480 | 2 battle | 0x1c0 | - | 0 | no | - | skipped | 0 | 0 | Caught by the orchestrator before starting a worker: it begins mid-function (`sb $v0, 0($s1)` with no prologue) and ends in another function's epilogue, so it's split wrong like func_800BFF38. Replaced with bc_object15/func_800C8E54 (same size). |
| 2026-11-28 | asm/ovl/battle/nonmatchings/bc_object15/func_800C8E54 | 2 battle | 0x1c0 | sonnet | 2 | no | 0 | matched | 1 | 0 | Rejected once: invented struct field names (mode, at, by, id, slot, vec) and a signed cast to test bit 15. Fields renamed to unkXX; the flag form didn't match (original uses lh/bgez), so the (s16) cast stays with a comment. Union member names (slot, sv, word) name the type views and were let through; a person should check them. |
| 2026-11-28 | asm/ovl/battle/nonmatchings/bc_object12/func_800C26B0 | 2 battle | 0x314 | sonnet | 15 | no | 0 | matched | 1 | 0 | Picked from outside the 400 list (largest there was 0x1c8). Worker also typed six globals, extended BattleEffectSlot/EffectStruct/EffectMesh and fixed casts in three neighbours, so the diff spans 8 files. Rejected once for new Doxygen comments in bc_object11.h; the orchestrator removed them itself rather than resending. Match needed nested ifs for the two flag tests so gcc wouldn't merge them. |
| 2026-11-28 | asm/ovl/effect_022/nonmatchings/effect_022/func_801A5DB8 | 9 effect | 0x3c | haiku | 1 | no | 0 | matched | 0 | 0 | Two-line function using the existing EffectEntity. The func_801A5820 prototype went into effect_022.h although only effect_022.c calls it; accepted because a static prototype for an INCLUDE_ASM function would warn, and the header already lists other such functions. |
| 2026-11-28 | asm/ovl/effect_022/nonmatchings/effect_022/func_801A66D4 | 9 effect | 0x114 | sonnet | 1 | no | 0 | matched | 0 | 0 | Matched on the first diff run. Uses a function-named struct view because EffectEntity disagrees at 0x6C and 0x74; a person may want to merge it with the views of its sibling task functions later. |
| 2026-11-28 | asm/ovl/effect_022/nonmatchings/effect_022/func_801A79A0 | 9 effect | 0x324 | sonnet | 1 | no | 0 | matched | 0 | 0 | Matched on the first diff run, helped by the existing EffectEntity, EffectModel and effectSpawnTask helpers. Small nits let through: the `radius` local is reused for the model-bottom height, and 0x380 sits beside decimal 384. |

Decisions made during the run:
- `pick.py next --count 400` returned only battle functions (no world or menu, no effects), and the biggest was 0x1c8. The five core picks are all battle. The larger one (func_800C26B0, 0x314) and the three effect picks (effect_022, the only split effect overlay with work left) came from the full list.
- func_800E1480 was swapped out before starting a worker because the asm starts mid-function. Eight functions went to workers.
- Where review only needed a deletion (new doc comments in func_800C26B0), the orchestrator made the fix itself instead of sending the work back.

## Run summary (2026-11-28, pilot 1)

- Functions given to workers: 8. Results: 6 matched, 1 blocked, 1 skipped (mis-split). One more mis-split function was found before a worker started, so 9 rows.
- `make full`: Match for every binary. Total warnings went from 997 to 995 (bc_object13.c 8 to 7, bc_object15.c 1 to 0).
- Matches per model: Haiku 2 of 3 tries (func_800B49D8, func_801A5DB8; func_800B3534 blocked). Sonnet 4 of 5 tries (func_800C8E54, func_800C26B0, func_801A66D4, func_801A79A0; func_800BFF38 mis-split).
- Match rate by size band, counting only functions that can be matched (blocked and mis-split left out):
  - under 0x100: 2 of 2 (3 tried)
  - 0x100-0x300: 2 of 2 (3 tried)
  - over 0x300: 2 of 2
- Haiku failed and Sonnet then succeeded: 0. No function needed a retry. Haiku's only failure (func_800B3534) can't be written in C at all.
- Hints: none given. No worker came back stuck with a diff of 20 or less. Diff runs per match: 1, 1, 1, 2, 4, 15.
- Review rejections: 3, spread over 3 of the 6 matches. Causes:
  - Invented names for struct fields (func_800C8E54).
  - Placement and typing: private structs next to the function, and a `void *` prototype (func_800B49D8).
  - New Doxygen comments in a header (func_800C26B0).
  After each rejection those rules went into the next worker's prompt, and later workers didn't repeat them.
- The main thing slowing the loop is the split, not the matching. Of the 129 battle functions of 0x100 bytes or more in the 400 list, 42 don't start with a stack-frame prologue. Some are leaf functions, but at least two (func_800BFF38, func_800E1480) are pieces of larger functions. pick.py could screen these out, or a person could fix the splat config for bc_object12 and bc_object22.
