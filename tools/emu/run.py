#!/usr/bin/env python3
"""Run disc 1 in PCSX-Redux without a window, play a schedule (see drive.lua), and turn
its screenshots into PNGs plus a contact sheet.

Usage:
    python3 tools/emu/run.py SCHEDULE --card emu/card.mcd [--trace emu/trace.txt]
                             [--out emu/out] [--sheet]

With --trace the run uses the interpreter and logs the listed functions (trace.lua).
The log is OUT/run.log.
"""
import argparse
import glob
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EMU = os.path.join(ROOT, "emu", "squashfs-root", "usr", "bin", "pcsx-redux")
HERE = os.path.dirname(os.path.abspath(__file__))


def write_png(path, width, height, rows):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\0" + bytes(r) for r in rows)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def rgb_rows(data, width, height, out_w=None, out_h=None):
    # Screenshots are 15-bit BGR, two bytes per pixel.
    out_w, out_h = out_w or width, out_h or height
    rows = []
    for y in range(out_h):
        sy = y * height // out_h
        row = bytearray()
        for x in range(out_w):
            i = (sy * width + x * width // out_w) * 2
            v = data[i] | data[i + 1] << 8
            row += bytes(((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3))
        rows.append(row)
    return rows


def convert_shots(out, log, sheet):
    sizes = dict((m.group(1), (int(m.group(2)), int(m.group(3))))
                 for m in re.finditer(r"SHOT (s\d+) (\d+) (\d+)", log))
    thumbs = []
    for raw in sorted(glob.glob(os.path.join(out, "shots", "*.raw"))):
        name = os.path.basename(raw)[:-4]
        width, height = sizes[name]
        data = open(raw, "rb").read()
        write_png(raw[:-4] + ".png", width, height, rgb_rows(data, width, height))
        if sheet:
            thumbs.append(rgb_rows(data, width, height, 160, 120))
        os.remove(raw)
    if thumbs:
        cols = 4
        rows_n = (len(thumbs) + cols - 1) // cols
        w, h = cols * 164, rows_n * 124
        canvas = [bytearray(w * 3) for _ in range(h)]
        for i, t in enumerate(thumbs):
            ox, oy = (i % cols) * 164, (i // cols) * 124
            for y in range(120):
                canvas[oy + y][ox * 3:(ox + 160) * 3] = t[y]
        write_png(os.path.join(out, "sheet.png"), w, h, canvas)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("schedule")
    p.add_argument("--card", required=True)
    p.add_argument("--trace")
    p.add_argument("--out", default=os.path.join(ROOT, "emu", "out"))
    p.add_argument("--sheet", action="store_true")
    p.add_argument("--timeout", type=int, default=1800)
    args = p.parse_args()

    cue = sorted(glob.glob(os.path.join(ROOT, "rom", "*.cue")))
    if not cue or not os.path.exists(EMU):
        sys.exit("needs rom/*.cue and emu/ (run tools/emu/setup.sh)")
    out = os.path.abspath(args.out)
    shutil.rmtree(os.path.join(out, "shots"), ignore_errors=True)
    os.makedirs(os.path.join(out, "shots"))

    env = dict(os.environ, EMU_SCHED=os.path.abspath(args.schedule), EMU_OUT=out)
    cmd = [EMU, "-no-ui", "-safe", "-testmode", "-noupdate", "-softgpu",
           "-memcard1=" + os.path.abspath(args.card), "-iso", cue[0], "-run"]
    if args.trace:
        env["EMU_TRACE"] = os.path.abspath(args.trace)
        cmd += ["-interpreter", "-debugger", "-dofile", os.path.join(HERE, "trace.lua")]
    else:
        cmd += ["-dynarec"]
    cmd += ["-dofile", os.path.join(HERE, "drive.lua")]

    with open(os.path.join(out, "run.log"), "w") as log:
        subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout, cwd=out)
    text = open(os.path.join(out, "run.log"), errors="replace").read()
    for line in text.splitlines():
        if "error" in line.lower():
            print(line)
    convert_shots(out, text, args.sheet)


if __name__ == "__main__":
    main()
