#!/usr/bin/env bash
# Prepare a fresh cloud container for the agent loop: toolchain, disc, verified build.
#
# Needs these environment variables (set them as secrets in the environment):
#   R2_ENDPOINT           https://<account_id>.r2.cloudflarestorage.com
#   R2_BUCKET             bucket name
#   FF8_DISC_PREFIX       key prefix holding the disc image(s), e.g. "ff8/"
#                         Every .bin/.img/.iso/.cue under it is copied into rom/.
#                         Disc 1 (SLUS-00892) is required; extract checks the SHA1.
#   AWS_ACCESS_KEY_ID     R2 access key
#   AWS_SECRET_ACCESS_KEY R2 secret key
#
# Run from the repo root: bash tools/agent/setup-cloud.sh

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

: "${R2_ENDPOINT:?set R2_ENDPOINT}"
: "${R2_BUCKET:?set R2_BUCKET}"
: "${FF8_DISC_PREFIX:?set FF8_DISC_PREFIX}"

SUDO=""
if [ "$(id -u)" != "0" ]; then SUDO="sudo"; fi

$SUDO apt-get update -qq
$SUDO apt-get install -y -qq binutils-mipsel-linux-gnu cpp make python3-venv cmake g++ >/dev/null

git submodule update --init --recursive --depth 1
chmod +x tools/gcc-2.7.2-cdk/cc1 tools/gcc-2.8.0-psx/cc1 tools/objdiff/objdiff 2>/dev/null || true

# Pull the disc from R2 with a throwaway venv so awscli never lands in the project venv.
if ! ls rom/*.bin rom/*.img rom/*.iso >/dev/null 2>&1; then
    python3 -m venv /tmp/awscli-venv
    /tmp/awscli-venv/bin/pip install -q awscli
    AWS_DEFAULT_REGION=auto /tmp/awscli-venv/bin/aws s3 cp \
        "s3://${R2_BUCKET}/${FF8_DISC_PREFIX}" rom/ \
        --recursive --endpoint-url "$R2_ENDPOINT" \
        --exclude "*" --include "*.bin" --include "*.img" --include "*.iso" --include "*.cue"
fi

# venv, extract (SHA1-checked), split, build, assets, expected, verify
make setup

# The game data must never be committed. rom/ and original/ are gitignored; check anyway.
if git status --porcelain --ignored=no | grep -E '^(\?\?|A ) (rom|original)/' ; then
    echo "game data is visible to git, refusing to continue" >&2
    exit 1
fi

echo "setup-cloud: build verified, ready for the agent loop"
