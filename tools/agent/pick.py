#!/usr/bin/env python3
"""Pick the next function for the agent loop and keep track of attempts.

The backlog is every INCLUDE_ASM in src/ (the vendored Psy-Q SDK is skipped).
State lives in agent/state.json, keyed by "<asm folder>/<function>", because
the same func_XXXXXXXX name can exist in several overlays.

Order follows the port: the core game first, effect overlays last. Inside a
tier, functions are taken smallest first, and an overlay that is nearly
finished goes before one that has barely started.

Only the effect overlays listed in EFFECTS in the Makefile are split, so the
rest have no asm yet. Their functions come out with "needs_split": true and
go after every function whose asm already exists in the same tier.

Functions whose asm doesn't look like a whole function are left out of
"next" and listed by "suspects": it reads saved registers it never set, has
an epilogue without a prologue (or the reverse), or doesn't end in a jump.
These are usually a piece of a larger function that splat cut wrongly, or
hand-written asm. Either way no worker can match them as they stand.

Usage:
    python3 tools/agent/pick.py next [--count N] [--max-attempts N]
    python3 tools/agent/pick.py record KEY --status STATUS [--model M]
                                       [--attempts N] [--best N] [--note TEXT]
    python3 tools/agent/pick.py stats
    python3 tools/agent/pick.py suspects

STATUS is one of: matched, nonmatching, stuck, skipped, in_progress.
"""
import argparse
import datetime
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STATE = os.path.join(ROOT, "agent", "state.json")
INCLUDE_RE = re.compile(r'INCLUDE_ASM\(\s*"([^"]+)"\s*,\s*([A-Za-z0-9_]+)\s*\)')
SIZE_RE = r"nonmatching\s+{name}\s*,\s*(0x[0-9A-Fa-f]+)"

# Lower number is picked first.
TIERS = [
    ("main", 0),
    ("ovl/field", 1),
    ("ovl/battle", 2),
    ("ovl/world", 3),
    ("ovl/menu", 4),
    ("ovl/", 5),
    ("ovl/effect_", 9),
]

STATUSES = ("matched", "nonmatching", "stuck", "skipped", "in_progress")


def load_state():
    if not os.path.exists(STATE):
        return {}
    with open(STATE) as f:
        return json.load(f)


def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f, indent=1, sort_keys=True)
        f.write("\n")


def binary_of(folder):
    parts = folder.split("/")
    if len(parts) > 2 and parts[1] == "ovl":
        return parts[2]
    return "main"


def tier_of(folder):
    rel = folder[len("asm/"):] if folder.startswith("asm/") else folder
    if not rel.startswith("ovl/"):
        return 0
    # Longest matching prefix wins, so "ovl/effect_" beats "ovl/".
    for prefix, tier in sorted(TIERS, key=lambda t: -len(t[0])):
        if rel.startswith(prefix):
            return tier
    return 5


def size_of(folder, name):
    path = os.path.join(ROOT, folder, name + ".s")
    if not os.path.exists(path):
        return None
    with open(path, errors="replace") as f:
        text = f.read()
    m = re.search(SIZE_RE.format(name=re.escape(name)), text)
    if m:
        return int(m.group(1), 16)
    # Fall back to counting instruction lines (4 bytes each).
    return 4 * sum(1 for line in text.splitlines() if re.match(r"\s*/\* [0-9A-F]+ ", line))


INS_RE = re.compile(r"/\* [0-9A-F]+ [0-9A-F]+ [0-9A-F]+ \*/\s+(\S+)\s*(.*)")
SAVED_RE = re.compile(r"\$(s[0-7]|fp)\b")
NO_DEST = ("sw", "sh", "sb", "swl", "swr", "beq", "bne", "beqz", "bnez", "bgez", "bltz",
           "blez", "bgtz", "jr", "jalr")


def suspect_reasons(folder, name):
    path = os.path.join(ROOT, folder, name + ".s")
    if not os.path.exists(path):
        return []
    ins = []
    for line in open(path, errors="replace"):
        m = INS_RE.search(line)
        if m and not m.group(1).startswith("."):
            ins.append((m.group(1), m.group(2)))
    if not ins:
        return []
    reasons = []
    prologue = any(op == "addiu" and a.startswith("$sp, $sp, -") for op, a in ins[:12])
    epilogue = any(op == "addiu" and re.match(r"\$sp, \$sp, 0x", a) for op, a in ins)
    if epilogue and not prologue:
        reasons.append("epilogue without prologue")
    if prologue and not epilogue:
        reasons.append("prologue without epilogue")
    if not prologue:
        written = set()
        for op, a in ins:
            ops = [x.strip() for x in a.split(",")]
            if not any(SAVED_RE.search(o) for o in ops):
                continue
            dest = [] if op in NO_DEST else SAVED_RE.findall(ops[0])
            srcs = [r for o in (ops if op in NO_DEST else ops[1:]) for r in SAVED_RE.findall(o)]
            unset = [r for r in srcs if r not in written]
            if unset:
                reasons.append("reads $%s before setting it" % unset[0])
                break
            written.update(dest)
    if not any(op in ("jr", "j", "b") for op, a in ins[-2:]):
        reasons.append("doesn't end in a jump")
    return reasons


def backlog():
    items = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "src")):
        if "psxsdk" in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.endswith(".c"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, errors="replace") as f:
                text = f.read()
            for m in INCLUDE_RE.finditer(text):
                folder, name = m.group(1), m.group(2)
                if "/psxsdk" in folder or folder.rstrip("/") == "asm/nonmatchings":
                    continue
                items.append({
                    "key": f"{folder}/{name}",
                    "folder": folder,
                    "name": name,
                    "file": os.path.relpath(path, ROOT),
                    "binary": binary_of(folder),
                })
    return items


def cmd_next(args):
    state = load_state()
    items = backlog()
    remaining = Counter(i["binary"] for i in items)
    candidates = []
    for item in items:
        entry = state.get(item["key"], {})
        status = entry.get("status")
        if status in ("skipped", "in_progress", "matched"):
            continue
        if status in ("stuck", "nonmatching") and entry.get("attempts", 0) >= args.max_attempts:
            continue
        item["size"] = size_of(item["folder"], item["name"])
        item["needs_split"] = item["size"] is None
        if not args.include_suspects and suspect_reasons(item["folder"], item["name"]):
            continue
        item["tier"] = tier_of(item["folder"])
        item["previous"] = entry or None
        candidates.append(item)
    # Never-tried before retried, then tier, then overlays already split, then
    # nearly-finished overlays, then small first.
    candidates.sort(key=lambda i: (
        i["previous"] is not None,
        i["tier"],
        i["needs_split"],
        remaining[i["binary"]],
        i["size"] if i["size"] is not None else 1 << 30,
        i["key"],
    ))
    print(json.dumps(candidates[:args.count], indent=1))


def cmd_record(args):
    state = load_state()
    entry = state.get(args.key, {})
    entry["status"] = args.status
    entry["attempts"] = entry.get("attempts", 0) + (args.attempts or 0)
    if args.model:
        entry["model"] = args.model
    if args.best is not None:
        entry["best_diff"] = args.best
    if args.note:
        entry.setdefault("notes", []).append(args.note)
        entry["notes"] = entry["notes"][-5:]
    entry["updated"] = datetime.date.today().isoformat()
    state[args.key] = entry
    save_state(state)
    print(json.dumps({args.key: entry}, indent=1))


def cmd_suspects(args):
    for item in backlog():
        reasons = suspect_reasons(item["folder"], item["name"])
        if reasons:
            print("%s: %s" % (item["key"], "; ".join(reasons)))


def cmd_stats(args):
    state = load_state()
    items = backlog()
    by_tier = Counter(tier_of(i["folder"]) for i in items)
    statuses = Counter(e.get("status") for e in state.values())
    print("backlog by tier (0 core ... 9 effects):", dict(sorted(by_tier.items())))
    print("backlog total:", len(items))
    unsplit = Counter(i["binary"] for i in items
                      if not os.path.exists(os.path.join(ROOT, i["folder"], i["name"] + ".s")))
    print("functions in overlays not split yet: %d (%d overlays)" % (sum(unsplit.values()), len(unsplit)))
    print("agent results:", dict(statuses))
    attempts = [e.get("attempts", 0) for e in state.values() if e.get("status") == "matched"]
    if attempts:
        print("mean attempts per match: %.1f" % (sum(attempts) / len(attempts)))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("next")
    n.add_argument("--count", type=int, default=1)
    n.add_argument("--max-attempts", type=int, default=3)
    n.add_argument("--include-suspects", action="store_true")
    r = sub.add_parser("record")
    r.add_argument("key")
    r.add_argument("--status", required=True, choices=STATUSES)
    r.add_argument("--model")
    r.add_argument("--attempts", type=int)
    r.add_argument("--best", type=int)
    r.add_argument("--note")
    sub.add_parser("stats")
    sub.add_parser("suspects")
    args = p.parse_args()
    {"next": cmd_next, "record": cmd_record, "stats": cmd_stats, "suspects": cmd_suspects}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
