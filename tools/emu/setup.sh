#!/usr/bin/env bash
# Download a pinned PCSX-Redux Linux build into emu/ and unpack it.
# Needs distrib.app reachable. Run from the repo root: bash tools/emu/setup.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

BUILD_PATH=/storage/assets/8ad/8a1/4f6/ea09b26550d2aeff64b4984201d40a458c3761d99cdb5f0addf2f94/PCSX-Redux-31cdf7ef-linux-x86_64.zip
BUILD_SHA1=6efc165bd1ef65723ff6057043fc8e5d48e9b706

mkdir -p emu
if [ ! -x emu/squashfs-root/usr/bin/pcsx-redux ]; then
    curl -fL "https://distrib.app${BUILD_PATH}" -o emu/pcsx-redux.zip
    echo "${BUILD_SHA1}  emu/pcsx-redux.zip" | sha1sum -c -
    (cd emu && unzip -oq pcsx-redux.zip && ./PCSX-Redux-HEAD-x86_64.AppImage --appimage-extract >/dev/null)
    rm -f emu/pcsx-redux.zip emu/PCSX-Redux-HEAD-x86_64.AppImage
fi
emu/squashfs-root/usr/bin/pcsx-redux -version | head -c 200
echo
