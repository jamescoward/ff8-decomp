#!/usr/bin/env python3
"""Turn the CALLS lines of a traced run into a Markdown table, one row per function that ran,
in order of first call. "In C" says whether src/ has C for it or still an INCLUDE_ASM.

Usage:
    python3 tools/emu/calls.py emu/out/run.log > emu/calls.md
"""
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CALLS_RE = re.compile(r"CALLS (\S+) count=(\d+) first=(\d+) last=(\d+) callers=(\S*)")


def source_files():
    asm, owner = set(), {}
    for path in glob.glob(os.path.join(ROOT, "src", "**", "*.c"), recursive=True):
        text = open(path, errors="replace").read()
        unit = os.path.relpath(path, os.path.join(ROOT, "src"))[:-2]
        for m in re.finditer(r'INCLUDE_ASM\("[^"]+",\s*(\w+)\)', text):
            asm.add(m.group(1))
            owner[m.group(1)] = unit
        for m in re.finditer(r"^[A-Za-z][^\n;=]*?\b(\w+)\([^;{]*\)\s*\{", text, re.M):
            owner.setdefault(m.group(1), unit)
    return asm, owner


def pattern(count, first, last):
    span = last - first + 1
    if count == 1:
        return "once"
    if span <= 30:
        return "short burst"
    rate = count / span
    if rate > 1.5:
        return "several per frame"
    if rate >= 0.7:
        return "about once a frame"
    return "now and then"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    asm, owner = source_files()
    rows = [m.groups() for m in CALLS_RE.finditer(open(sys.argv[1], errors="replace").read())]
    rows.sort(key=lambda r: (int(r[2]), r[0]))
    print("| function | file | in C | calls | first frame | last frame | pattern | called from |")
    print("|---|---|---|---|---|---|---|---|")
    for name, count, first, last, callers in rows:
        count, first, last = int(count), int(first), int(last)
        print("| %s | %s | %s | %d | %d | %d | %s | %s |" % (
            name, owner.get(name, "?"), "no" if name in asm else "yes", count, first, last,
            pattern(count, first, last), callers.replace(",", ", ")))


if __name__ == "__main__":
    main()
