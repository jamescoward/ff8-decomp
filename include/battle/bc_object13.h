#ifndef BATTLE_BC_OBJECT13_H
#define BATTLE_BC_OBJECT13_H

#include "common.h"
#include "psxsdk/libgte.h"

void func_800C42DC(void);
/**
 * @file
 * @brief Battle sound sequences.
 */

/** @brief Publish the two tables inside @p base for the sequencer to read. */
void func_800C3BE0(u8 *base);

/** @brief Queue the AKAO sequence at @p sequence for playback. */
void func_800C4764(u8 *sequence, s32 arg1, s32 arg2);

s32 func_800C2CBC(s32 arg0, void *arg1, void *arg2, void *arg3);

void func_800C48A8(struct BattleEffectSlot *arg0, s32 arg1, s32 arg2, SVECTOR *arg3);

/** @brief Reset @p slot when its entity's flags call for it. */
s32 func_800C2BD0(struct BattleEffectSlot *slot, s32 arg1);

#endif /* BATTLE_BC_OBJECT13_H */
