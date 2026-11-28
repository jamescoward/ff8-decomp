#include "common.h"
#include "battle.h"
#include "psxsdk/libgte.h"
#include "effect.h"
#include "battle/bc_object8.h"
#include "battle/bc_object11.h"
#include "battle/bc_object12.h"
#include "battle/bc_object13.h"
#include "battle/bc_object9.h"

#define EFFECT_STRUCT_FLAG_UNK01 0x1
#define EFFECT_STRUCT_FLAG_UNK02 0x2
#define EFFECT_STRUCT_FLAG_UNK04 0x4
#define EFFECT_STRUCT_FLAG_UNK08 0x8
#define EFFECT_STRUCT_FLAG_UNK40 0x40
#define FUNC_800C26B0_SLOT_FLAG_UNK08 0x8

extern BattleEffectSlot *D_800F1A54;
extern u8 *D_800F1A58;
extern EffectStruct *D_800F1A5C;
extern BattleEffectSlot *D_800F1A60;
extern u8 *D_800F1A68;
extern u8 D_800E3F52;
s32 func_800C0CB8(BattleEffectSlot *, s32);
s32 func_800C112C(s16);
void func_800C15EC(s16, s32);
s32 func_800C197C(s32, u8 **);
void func_800C29C4(s32, s32);
s32 func_800BD3A0(void);
void func_800BD230(void);

/**
 * @brief Process render state machine for an entity.
 *
 * Reads state byte at offset 0xD of the entity. In state 0, calls
 * func_800BD3A0 to search for available render slots; if none found
 * (returns 0), advances to state 1. In state 1, calls func_800BD230
 * and writes 0xFF to byte 1 of the pointer at offset 0x10, returning 2.
 *
 * @param a0 Pointer to entity state structure.
 * @return 0 if slot search found a match, 2 if render setup completed.
 */
s32 func_800BF0E8(u8 *a0) {
    u8 state = a0[0xD];
    u8 *ptr = *(u8 **)(a0 + 0x10);

    switch (state) {
    case 0:
        if (func_800BD3A0() != 0) {
            return 0;
        }
        a0[0xD] = a0[0xD] + 1;
    case 1:
        func_800BD230();
        *(u8 *)(ptr + 1) = 0xFF;
        return 2;
    }
}

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF168);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF308);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF3D8);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF444);


INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF5C4);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF7E8);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF888);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF92C);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF95C);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF9CC);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BF9EC);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BFA58);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BFBA8);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BFC14);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BFDA0);


INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BFE1C);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BFEC8);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BFEF8);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800BFF38);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C0098);

/**
 * @brief Call func_800BFE1C for each of count entries at stride 0x18.
 *
 * Iterates count times, calling func_800BFE1C with a pointer that
 * advances by 0x18 bytes each iteration.
 *
 * @param ptr Base pointer to first entry.
 * @param count Number of entries to process.
 */
void func_800C00D8(u8 *ptr, s32 count) {
    s32 i = 0;
    while (i < count) {
        u8 *cur = ptr;
        ptr += 0x18;
        func_800BFE1C(cur);
        i++;
    }
}

extern u8 D_800F1940[];
extern u8 D_800F16C0[];

/**
 * @brief Initialize D_800F1940 buffer via func_800B2A00 and return it.
 *
 * Calls func_800B2A00 with D_800F1940, D_800F16C0, size 0x20, and count 0x14.
 *
 * @return Pointer to D_800F1940.
 */
u8 *func_800C0134(void) {
    u8 *buf = D_800F1940;
    func_800B2A00(buf, D_800F16C0, 0x20, 0x14);
    return buf;
}

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C0178);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C01A4);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C02D4);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C03DC);

/**
 * @brief Clear 9 halfwords in a 3x3 structure.
 *
 * Outer loop iterates 3 rows (stride 6). Inner loop clears 3 halfwords
 * per row starting at offset 4 and going backwards.
 *
 * @param a0 Base pointer to structure.
 */
void func_800C0780(s32 a0) {
    s32 j = 0;
outer:
    {
        s32 i = 2;
        s32 ptr = a0 + 4;
        do {
            *(s16 *)ptr = 0;
            i--;
            ptr -= 2;
        } while (i >= 0);
    }
    j++;
    a0 += 6;
    if (j < 3) goto outer;
}

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C07B4);

/**
 * @brief Look up a sound entry and start playback if found.
 *
 * Sign-extends a0 to 16 bits and calls func_800C07B4 to look up
 * the entry. If not found (returns 0), returns 0. Otherwise fills
 * a local buffer with the result and calls ScaleMatrix.
 *
 * @param a0 Sound ID (sign-extended to s16).
 * @param a1 Playback parameter.
 * @return a1 if playback started, 0 if entry not found.
 */
s32 func_800C0AE4(s32 a0, s32 a1) {
    VECTOR buf;
    s32 result = func_800C07B4((s16)a0);
    if (result != 0) {
        buf.vz = result;
        buf.vy = result;
        buf.vx = result;
        ScaleMatrix((MATRIX *)a1, &buf);
        return a1;
    }
    return 0;
}

/**
 * @brief Look up sound, compute inverse ratio, and start playback.
 *
 * Sign-extends a0, looks up sound via func_800C07B4. If found,
 * calls TransposeMatrix with a1, computes 0x1000000 / result,
 * fills a buffer with the quotient, and calls ScaleMatrix.
 *
 * @param a0 Sound ID (sign-extended to s16).
 * @param a1 Playback parameter.
 * @return a1 if playback started, 0 if entry not found.
 */
s32 func_800C0B3C(s32 a0, s32 a1) {
    VECTOR buf;
    s32 result = func_800C07B4((s16)a0);
    if (result != 0) {
        s32 quotient;
        TransposeMatrix((MATRIX *)a1, (MATRIX *)a1);
        quotient = 0x1000000 / result;
        buf.vz = quotient;
        buf.vy = quotient;
        buf.vx = quotient;
        ScaleMatrix((MATRIX *)a1, &buf);
        return a1;
    }
    return 0;
}

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C0BB8);

/**
 * @brief Check if a table entry at the given index is valid.
 *
 * Loads a table pointer from a0->0x64->0xC. If the table's first
 * halfword (count) is less than a1, returns 0. Otherwise checks
 * the halfword at index a1; returns 1 if non-zero, 0 if zero.
 *
 * @param a0 Entity pointer with table reference at offset 0x64.
 * @param a1 Table index to check.
 * @return 1 if entry is valid, 0 otherwise.
 */
INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C0CB8);

/**
 * @brief Store byte to D_800F1A5C target, then look up address from table.
 *
 * Stores a0 to the byte pointed to by D_800F1A5C. Then reads a table base
 * pointer from D_800F1A54->0x64->0xC, uses a0 as an index into a u16 offset
 * table, and returns the base pointer plus that offset.
 *
 * @param a0 Index value (also stored as byte).
 * @return Resolved pointer from table lookup.
 */
s32 func_800C0D00(s32 a0) {
    u16 *table;
    D_800F1A5C->unk0 = a0;
    table = D_800F1A54->mesh->unk00C;
    a0 &= 0xFF;
    return (s32)table + table[a0];
}

/**
 * @brief Process animation command from D_800F1A5C.
 *
 * Reads the byte at offset 3 of the pointer stored in D_800F1A5C.
 * If non-zero, calls func_800C0CB8 with D_800F1A54 and the byte.
 * If that succeeds, reads and returns the byte, clearing it.
 * Otherwise calls func_800B5604 with D_800F1A54 and returns the
 * result masked to 8 bits.
 *
 * @return Processed command byte or fallback value.
 */
s32 func_800C0D3C(void) {
    EffectStruct *ptr = D_800F1A5C;
    if (ptr->unk3 != 0) {
        if (func_800C0CB8(D_800F1A54, ptr->unk3) != 0) {
            EffectStruct *ptr2 = D_800F1A5C;
            s32 val = ptr2->unk3;
            ptr2->unk3 = 0;
            return val;
        }
    }
    return (u8)func_800B5604(D_800F1A54);
}

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C0DB0);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C0FD4);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C112C);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C15EC);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C197C);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C22A8);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C2528);

// The script address is kept as an integer because func_800C2CBC takes and returns it that way.
void func_800C26B0(BattleEffectSlot *arg0) {
    SVECTOR sp10;
    u16 *table;
    s32 cursor;
    s32 start;
    EffectStruct *entity;
    u16 flags;

    D_800F1A54 = arg0;
    D_800F1A58 = arg0->unk06C;
    entity = arg0->unk074;
    D_800F1A5C = entity;
    table = arg0->mesh->unk00C;
    if (entity->unk2B != 0 && !(arg0->unk02 & FUNC_800C26B0_SLOT_FLAG_UNK08)) {
        start = (s32)table + table[entity->unk2B];
        D_800F1A68 = entity->unk30;
        func_800C2CBC(start, func_800C197C, func_800C112C, func_800C15EC);
    }
    D_800F1A68 = D_800F1A5C->unk4;
    do {
        entity = D_800F1A5C;
        table = arg0->mesh->unk00C;
        start = (s32)table + table[entity->unk0];
        cursor = start + entity->unk2E;
        if (entity->unk2C & EFFECT_STRUCT_FLAG_UNK01) {
            entity->unk2C &= ~EFFECT_STRUCT_FLAG_UNK01;
            cursor = func_800C2CBC(cursor, func_800C197C, func_800C112C, func_800C15EC);
            flags = D_800F1A5C->unk2C;
            if (!(flags & EFFECT_STRUCT_FLAG_UNK01)) {
                if (!(flags & EFFECT_STRUCT_FLAG_UNK02)) {
                    if (func_800BD06C(D_800F1A54) != 0) {
                        func_800BD0B4(D_800F1A54, *D_800F1A58);
                        D_800F1A5C->unk2C |= EFFECT_STRUCT_FLAG_UNK02;
                    }
                }
            }
        } else {
            if (func_800BD06C(D_800F1A54) != 0) {
                func_800BC7D4(D_800F1A54);
                D_800F1A5C->unk2C = (D_800F1A5C->unk2C | EFFECT_STRUCT_FLAG_UNK04) & ~EFFECT_STRUCT_FLAG_UNK08;
            } else {
                D_800F1A5C->unk2C &= ~EFFECT_STRUCT_FLAG_UNK04;
            }
            if (!(D_800F1A5C->unk2C & EFFECT_STRUCT_FLAG_UNK08)) {
                if (D_800F1A5C->unk1 == 0) {
                    cursor = func_800C2CBC(cursor, func_800C197C, func_800C112C, func_800C15EC);
                } else {
                    D_800F1A5C->unk1--;
                }
            }
        }
    } while (cursor == 0);
    start = (s32)table + table[D_800F1A5C->unk0];
    D_800F1A5C->unk2E = cursor - start;
    if (D_800F1A5C->unk3 != 0 && (D_800F1A5C->unk2C & EFFECT_STRUCT_FLAG_UNK40)) {
        func_800C2AB0(D_800F1A54, D_800F1A5C->unk3);
    }
    if (D_800E3F52 != 0) {
        func_800B3960(D_800F1A60, 0xF1, 0, &sp10);
        func_800C48A8(D_800F1A60, D_800F1A60->unk4 == 0, 0, &sp10);
        D_800E3F52 = 0;
    }
    D_800F1A5C->unk2A++;
}




INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C29C4);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C2A18);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C2A38);

INCLUDE_ASM("asm/ovl/battle/nonmatchings/bc_object12", func_800C2AB0);
