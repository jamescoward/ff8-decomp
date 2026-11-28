#!/usr/bin/env python3
"""Turn a memory card file into the raw 128 KiB image PCSX-Redux loads, and list its saves.

Raw cards (.mcd, .mcr, .mc, .srm) are copied as they are. DexDrive (.gme) and
VGS (.vgs, .mem) cards have a header in front of the raw image, which is dropped.

Usage:
    python3 tools/emu/card.py IN_FILE OUT.mcd
"""
import sys

CARD_SIZE = 0x20000
HEADERS = {b"123-456-STD": 0xF40, b"VgsM": 0x40}


def raw_card(data):
    for magic, size in HEADERS.items():
        if data.startswith(magic):
            data = data[size:]
            break
    card = data[:CARD_SIZE]
    if len(card) != CARD_SIZE or card[:2] != b"MC":
        sys.exit("not a PlayStation memory card image")
    return card


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    card = raw_card(open(sys.argv[1], "rb").read())
    open(sys.argv[2], "wb").write(card)
    for slot in range(1, 16):
        entry = card[slot * 128:(slot + 1) * 128]
        if entry[0] == 0x51:
            code = entry[10:30].split(b"\0")[0].decode("ascii", "replace")
            title = card[slot * 0x2000 + 4:slot * 0x2000 + 68].decode("shift_jis", "replace").strip()
            print(f"block {slot}: {code} {title}")


if __name__ == "__main__":
    main()
