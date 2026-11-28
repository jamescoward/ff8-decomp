#!/usr/bin/env python3
"""Write a trace list for trace.lua: every function in one binary's symbols file,
with the first bytes of its code taken from the original binary.

Usage:
    python3 tools/emu/sigs.py BINARY [--only NAME ...] > emu/trace.txt
"""
import argparse
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SIG_BYTES = 12


def segment(binary):
    text = open(os.path.join(ROOT, "config", "ff8.yaml")).read()
    m = re.search(r"^- name: %s\n(.*?)(?=^- name: |\Z)" % re.escape(binary), text, re.M | re.S)
    if not m:
        sys.exit("no binary %s in config/ff8.yaml" % binary)
    block = m.group(1)
    target = re.search(r"target_path: (\S+)", block).group(1)
    start = int(re.search(r"start: (0x[0-9A-Fa-f]+)", block).group(1), 16)
    vram = int(re.search(r"vram: (0x[0-9A-Fa-f]+)", block).group(1), 16)
    return target, start, vram


def main():
    p = argparse.ArgumentParser()
    p.add_argument("binary")
    p.add_argument("--only", nargs="*")
    args = p.parse_args()
    target, start, vram = segment(args.binary)
    data = open(os.path.join(ROOT, target), "rb").read()
    syms = os.path.join(ROOT, "config", "symbols.%s.txt" % args.binary)
    for line in open(syms):
        m = re.match(r"(\w+) = 0x([0-9A-Fa-f]+);.*type:func", line)
        if not m or (args.only and m.group(1) not in args.only):
            continue
        addr = int(m.group(2), 16)
        off = addr - vram + start
        if not 0 <= off < len(data) - SIG_BYTES:
            continue
        print("%08X %s %s" % (addr, data[off:off + SIG_BYTES].hex(), m.group(1)))


if __name__ == "__main__":
    main()
