#!/usr/bin/env python3
"""Reject matches that cheat, or that would get in the way of a port.

Looks only at lines the change adds (git diff against BASE, default origin/main)
under src/, include/ and config/. Errors fail the run; warnings go to the
reviewer, who decides.

Usage:
    python3 tools/agent/lint.py [--base REF]
"""
import argparse
import re
import subprocess
import sys

ERRORS = [
    # Raw PSX RAM, scratchpad or hardware register addresses instead of symbols.
    (re.compile(r"\b0x(80|A0|1[fF]80)[0-9A-Fa-f]{4,6}\b"), "raw PSX address; use a symbol"),
    (re.compile(r"\b(__asm__|asm)\s*(volatile\s*)?\("), "inline asm"),
    (re.compile(r"\bregister\b.*\b(asm|__asm__)\s*\("), "register pinning"),
    (re.compile(r"\bNONMATCHING\b"), "use the guarded NON_MATCHING form (see AGENTS.md)"),
    (re.compile(r"for\s*\(\s*;\s*;\s*\)"), "write endless loops as while (1)"),
    (re.compile(r"^\s+extern\b"), "extern inside a function body; include the owner's header"),
    (re.compile(r"Co-Authored-By|Generated with", re.I), "AI attribution"),
]

WARNINGS = [
    (re.compile(r"\bvolatile\b"), "volatile: needed, or forcing a match?"),
    (re.compile(r"\bregister\b"), "register keyword"),
    (re.compile(r"\(\s*(u8|s8|u16|s16|u32|s32|char|short|int|long)\s*\*\s*\)\s*\(?\s*\w+\s*\+\s*0x"),
     "pointer arithmetic with a raw offset; use a struct field"),
    (re.compile(r"—|→"), "em dash or arrow in a comment"),
    (re.compile(r"\bdo\s*\{\s*\}\s*while\s*\(\s*0\s*\)"), "empty do-while, a match trick?"),
]

GOTO_LIMIT = 2


def added_lines(base):
    diff = subprocess.run(
        ["git", "diff", "-U0", base, "--", "src", "include", "config"],
        capture_output=True, text=True, check=True).stdout
    path, lineno = None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            lineno = int(re.search(r"\+(\d+)", line).group(1))
        elif line.startswith("+") and path:
            yield path, lineno, line[1:]
            lineno += 1
        elif line.startswith("-") and not line.startswith("--- ") and path and path.startswith("config/symbols"):
            yield path, 0, "\0REMOVED " + line[1:]


def strip_comment(code):
    code = re.sub(r"/\*.*?\*/", "", code)
    return code.split("//")[0]


def check_guards(path):
    """Every #ifdef NON_MATCHING must keep the INCLUDE_ASM in its #else."""
    problems = []
    try:
        lines = open(path, errors="replace").read().splitlines()
    except OSError:
        return problems
    i = 0
    while i < len(lines):
        if re.match(r"\s*#\s*ifdef\s+NON_MATCHING\b", lines[i]):
            start, depth, saw_else, saw_asm = i, 1, False, False
            i += 1
            while i < len(lines) and depth:
                l = lines[i]
                if re.match(r"\s*#\s*if", l):
                    depth += 1
                elif re.match(r"\s*#\s*endif", l):
                    depth -= 1
                elif depth == 1 and re.match(r"\s*#\s*else", l):
                    saw_else = True
                elif saw_else and "INCLUDE_ASM" in l:
                    saw_asm = True
                i += 1
            if not (saw_else and saw_asm):
                problems.append((path, start + 1, "NON_MATCHING block without #else INCLUDE_ASM"))
            continue
        i += 1
    return problems


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="origin/main")
    args = p.parse_args()

    errors, warnings, gotos, touched = [], [], {}, set()
    for path, n, text in added_lines(args.base):
        if path.startswith("config/symbols"):
            # Names need a human to verify them in the running game.
            if text.startswith("\0REMOVED "):
                old = text[len("\0REMOVED "):]
                if not re.match(r"\s*(func|D|jtbl|L)_[0-9A-Fa-f]+\b", old):
                    errors.append((path, n, "verified name removed or changed: " + old.strip()))
            elif not re.match(r"\s*((func|D|jtbl|L)_[0-9A-Fa-f]+\s*=|//|$)", text):
                errors.append((path, n, "new name in symbols file; names need human verification"))
            continue
        touched.add(path)
        code = strip_comment(text)
        for rx, msg in ERRORS:
            target = text if "attribution" in msg or "dash" in msg else code
            if rx.search(target):
                errors.append((path, n, msg))
        for rx, msg in WARNINGS:
            target = text if "dash" in msg else code
            if rx.search(target):
                warnings.append((path, n, msg))
        if re.search(r"\bgoto\b", code):
            gotos[path] = gotos.get(path, 0) + 1

    for path, count in gotos.items():
        if count > GOTO_LIMIT:
            warnings.append((path, 0, f"{count} new gotos"))
    for path in touched:
        if path.endswith((".c", ".h")):
            errors.extend(check_guards(path))

    for kind, items in (("error", errors), ("warning", warnings)):
        for path, n, msg in items:
            print(f"{kind}: {path}:{n}: {msg}")
    print(f"lint: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
