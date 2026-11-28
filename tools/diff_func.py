#!/usr/bin/env python3
"""Diff one function between two MIPS object files.

Usage: diff_func.py --target target.o --base current.o <symbol>

Prints the two disassemblies side by side, then either "MATCH" or how many
instructions differ. Exits 0 on a match, 1 on a difference, 2 on an error.
"""

import argparse
import difflib
import re
import subprocess
import sys

OBJDUMP = "mipsel-linux-gnu-objdump"

INSN_RE = re.compile(r"^\s*([0-9a-f]+):\t(.*)$")
RELOC_RE = re.compile(r"^\s*([0-9a-f]+): (R_MIPS_\w+)\s+(\S+)")
START_RE = re.compile(r"^([0-9a-f]+) <(.+)>:$")
BRANCH_TARGET_RE = re.compile(r"\b([0-9a-f]+) <[^>]+>")

RELOC_FORMAT = {
    "R_MIPS_HI16": "%hi({})",
    "R_MIPS_LO16": "%lo({})",
    "R_MIPS_GPREL16": "%gp_rel({})",
    "R_MIPS_26": "{}",
    "R_MIPS_32": "{}",
}


def disassemble(path, symbol):
    try:
        out = subprocess.run(
            [OBJDUMP, "-dr", "-z", "--no-show-raw-insn", f"--disassemble={symbol}", path],
            check=True, capture_output=True, text=True,
        ).stdout
    except FileNotFoundError:
        sys.exit(f"error: {OBJDUMP} not found")
    except subprocess.CalledProcessError as e:
        sys.exit(f"error: objdump failed on {path}:\n{e.stderr}")

    start = None
    insns = []
    for line in out.splitlines():
        m = START_RE.match(line)
        if m:
            start = int(m.group(1), 16)
            continue
        if start is None:
            continue
        m = RELOC_RE.match(line)
        if m and insns:
            fmt = RELOC_FORMAT.get(m.group(2), m.group(2) + "({})")
            insns[-1] = (insns[-1][0], insns[-1][1] + "  ; " + fmt.format(m.group(3)))
            continue
        m = INSN_RE.match(line)
        if m:
            addr = int(m.group(1), 16) - start
            text = m.group(2).strip().replace("\t", " ")
            # Branch targets are section offsets; make them relative to the function.
            text = BRANCH_TARGET_RE.sub(
                lambda b: "." + format(int(b.group(1), 16) - start, "+#x"), text)
            insns.append((addr, text))
    if start is None:
        sys.exit(f"error: symbol {symbol} not found in {path}")
    return insns


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("symbol")
    args = ap.parse_args()

    target = disassemble(args.target, args.symbol)
    base = disassemble(args.base, args.symbol)
    t_text = [t for _, t in target]
    b_text = [t for _, t in base]

    width = max([len(t) for t in t_text] + [20]) + 2
    print(f"     {'TARGET':<{width}}   BASE")
    differ = 0
    sm = difflib.SequenceMatcher(None, t_text, b_text, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                print(f"{target[i1 + k][0]:4x} {t_text[i1 + k]:<{width}}   {b_text[j1 + k]}")
            continue
        n = max(i2 - i1, j2 - j1)
        differ += n
        for k in range(n):
            t = t_text[i1 + k] if i1 + k < i2 else ""
            b = b_text[j1 + k] if j1 + k < j2 else ""
            mark = {"replace": "|", "delete": "<", "insert": ">"}[op]
            addr = f"{target[i1 + k][0]:4x}" if i1 + k < i2 else "    "
            print(f"{addr} {t:<{width}} {mark} {b}")

    print()
    if differ == 0:
        print("MATCH")
        return 0
    print(f"{differ} instruction(s) differ (target {len(target)}, base {len(base)})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
