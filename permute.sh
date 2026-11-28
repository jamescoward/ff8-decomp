#!/usr/bin/env bash
# Setup and optionally run decomp-permuter for a given function.
#
# Usage:
#   ./permute.sh <function_name>              # auto-finds .s and source
#   ./permute.sh --asm-dir <folder> <function_name>
#                                             # needed when overlays share the name
#   ./permute.sh --run [-j N] <function_name> # setup + run permuter
#
# Example:
#   ./permute.sh func_8009B6D0
#   ./permute.sh --run -j4 func_80021358

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PERMUTER_DIR="${SCRIPT_DIR}/tools/decomp-permuter"
WORK_DIR="${SCRIPT_DIR}/permuter"

# Toolchain (must match Makefile)
CPP="/usr/bin/cpp"
PSYQ41_CC1="${SCRIPT_DIR}/tools/gcc-2.7.2-cdk/cc1"
PSYQ43_CC1="${SCRIPT_DIR}/tools/gcc-2.8.0-psx/cc1"
MASPSX="python3 ${SCRIPT_DIR}/tools/maspsx/maspsx.py"
AS="mipsel-linux-gnu-as"

ASFLAGS="-march=r3000 -mabi=32 -EL -no-pad-sections -O0 -Iinclude"

# Per-file compiler settings, read from the Makefile so they can't fall behind it.
makefile_var() {
    awk -v name="$1" '
        !found && $0 ~ "^" name "[ \t]*:?=" { found = 1; sub("^[^=]*=", "") }
        found {
            line = $0
            sub("#.*$", "", line)
            more = (line ~ /\\[ \t]*$/)
            sub("\\\\[ \t]*$", "", line)
            printf "%s ", line
            if (!more) exit
        }' "${SCRIPT_DIR}/Makefile"
}
NO_G0_SRCS="$(makefile_var NO_G0_SRCS)"
G4_SRCS="$(makefile_var G4_SRCS)"
O0_SRCS="$(makefile_var O0_SRCS)"
PSYQ43_SRCS="$(makefile_var PSYQ43_SRCS)"
NO_EXPAND_DIV="$(makefile_var NO_EXPAND_DIV)"
EXPAND_DIV_SRCS="$(makefile_var EXPAND_DIV_SRCS)"

in_list() {
    local item="$1" entry
    shift
    for entry in $*; do
        [[ "${entry}" == "${item}" ]] && return 0
    done
    return 1
}

SRC_FILE=""
ASM_SUBDIR=""
PSYQ_VER=""

# Parse arguments
RUN=0
PERMUTER_ARGS=()
FUNC_NAME=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --run)
            RUN=1
            shift
            ;;
        -j*)
            PERMUTER_ARGS+=("$1")
            shift
            ;;
        --src)
            SRC_FILE="$2"
            shift 2
            ;;
        --asm-dir)
            ASM_SUBDIR="$2"
            shift 2
            ;;
        --psyq)
            PSYQ_VER="$2"
            shift 2
            ;;
        -*)
            PERMUTER_ARGS+=("$1")
            shift
            ;;
        *)
            FUNC_NAME="$1"
            shift
            ;;
    esac
done

if [[ -z "${FUNC_NAME}" ]]; then
    echo "Usage: $0 [--run] [-j N] [--asm-dir <folder>] [--src <file.c>] [--psyq 4.1|4.3] <function_name>"
    exit 1
fi

# Auto-find the .s file if --asm-dir not given. Overlays can share function
# names, so refuse to guess when there is more than one.
if [[ -z "${ASM_SUBDIR}" ]]; then
    S_FILES="$(find asm -path '*/nonmatchings/*' -name "${FUNC_NAME}.s" 2>/dev/null | sort)"
    if [[ -z "${S_FILES}" ]]; then
        echo "Error: ${FUNC_NAME}.s not found under asm/"
        exit 1
    fi
    if [[ "$(echo "${S_FILES}" | wc -l)" -gt 1 ]]; then
        echo "Error: ${FUNC_NAME}.s exists in more than one place; pass --asm-dir with one of:"
        echo "${S_FILES}" | xargs -n1 dirname | sed 's/^/  /'
        exit 1
    fi
    ASM_SUBDIR="$(dirname "${S_FILES}")"
fi
ASM_SUBDIR="${ASM_SUBDIR%/}"

TARGET_ASM="${ASM_SUBDIR}/${FUNC_NAME}.s"
if [[ ! -f "${TARGET_ASM}" ]]; then
    echo "Error: assembly file not found: ${TARGET_ASM}"
    exit 1
fi

# Find the source file holding this function's INCLUDE_ASM if --src not given
if [[ -z "${SRC_FILE}" ]]; then
    SRC_FILE="$(grep -rlE "INCLUDE_ASM\(\"${ASM_SUBDIR}\", *${FUNC_NAME}\)" src 2>/dev/null | head -1 || true)"
    if [[ -z "${SRC_FILE}" ]]; then
        echo "Error: no INCLUDE_ASM(\"${ASM_SUBDIR}\", ${FUNC_NAME}) found under src/"
        echo "Use --src to specify explicitly."
        exit 1
    fi
fi

if [[ ! -f "${SRC_FILE}" ]]; then
    echo "Error: source file not found: ${SRC_FILE}"
    exit 1
fi

# The binary is the overlay directory under asm/ovl/, else the main executable
if [[ "${ASM_SUBDIR}" == asm/ovl/* ]]; then
    BINARY="$(echo "${ASM_SUBDIR}" | cut -d/ -f3)"
else
    BINARY="SLUS_008.92"
fi

# Verify the permuter is available
if [[ ! -f "${PERMUTER_DIR}/permuter.py" ]]; then
    echo "Error: decomp-permuter not found. Run: git submodule update --init tools/decomp-permuter"
    exit 1
fi

# Auto-detect PsyQ version from source file if not specified
if [[ -z "${PSYQ_VER}" ]]; then
    PSYQ_VER="4.1"
    if in_list "${SRC_FILE}" ${PSYQ43_SRCS}; then
        PSYQ_VER="4.3"
    fi
fi

# Select compiler based on PsyQ version
case "${PSYQ_VER}" in
    4.1)
        CC1="${PSYQ41_CC1}"
        ASPSX_VER="2.67"
        ;;
    4.3)
        CC1="${PSYQ43_CC1}"
        ASPSX_VER="2.77"
        ;;
    *)
        echo "Error: unsupported PsyQ version '${PSYQ_VER}' (use 4.1 or 4.3)"
        exit 1
        ;;
esac

# Auto-detect compile flags based on source file
COMPILE_FLAGS="-O2 -G0"
if in_list "${SRC_FILE}" ${NO_G0_SRCS}; then
    COMPILE_FLAGS="-O2"
fi
if in_list "${SRC_FILE}" ${G4_SRCS}; then
    COMPILE_FLAGS="-O2 -G4"
fi
if in_list "${SRC_FILE}" ${O0_SRCS}; then
    COMPILE_FLAGS="-O0 -G0"
    ASPSX_VER="2.56"
fi

ASPSX_FLAGS="--aspsx-version=${ASPSX_VER}"

# Division expansion follows the Makefile's expand_div rule
if in_list "${SRC_FILE}" ${EXPAND_DIV_SRCS}; then
    ASPSX_FLAGS="${ASPSX_FLAGS} --expand-div"
elif [[ "${BINARY}" == effect_* ]] && ! in_list "${BINARY}" ${NO_EXPAND_DIV}; then
    ASPSX_FLAGS="${ASPSX_FLAGS} --expand-div"
fi

echo "Setting up permuter for ${FUNC_NAME} (PsyQ ${PSYQ_VER}, flags: ${COMPILE_FLAGS}, maspsx: ${ASPSX_FLAGS})..."
echo "  Source:  ${SRC_FILE}"
echo "  Asm dir: ${ASM_SUBDIR}"

# Create working directory
FUNC_DIR="${WORK_DIR}/${FUNC_NAME}"
mkdir -p "${FUNC_DIR}"

# --- settings.toml ---
cat > "${FUNC_DIR}/settings.toml" <<EOF
func_name = "${FUNC_NAME}"
compiler_type = "gcc"
EOF

# --- compile.sh ---
cat > "${FUNC_DIR}/compile.sh" <<'COMPILE_EOF'
#!/usr/bin/env bash
# Compile script for decomp-permuter
# Usage: ./compile.sh input.c -o output.o
set -euo pipefail

INPUT="$1"
shift
# Parse -o flag
OUTPUT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        -o) OUTPUT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "${OUTPUT}" ]]; then
    echo "Error: -o flag required"
    exit 1
fi

COMPILE_EOF

# Append the toolchain paths using the resolved script dir
cat >> "${FUNC_DIR}/compile.sh" <<EOF
DIR="${SCRIPT_DIR}"
CPP="/usr/bin/cpp"
CC1="${CC1}"
MASPSX="python3 ${SCRIPT_DIR}/tools/maspsx/maspsx.py"
ASPSX_FLAGS="${ASPSX_FLAGS}"
COMPILE_FLAGS="${COMPILE_FLAGS}"
AS="mipsel-linux-gnu-as"
ASFLAGS="-march=r3000 -mabi=32 -EL -no-pad-sections -O0 -I${SCRIPT_DIR}/include"
EOF

cat >> "${FUNC_DIR}/compile.sh" <<'COMPILE_EOF'

# Resolve input/output to absolute paths before changing directories
INPUT_ABS="$(realpath "${INPUT}")"
OUTPUT_ABS="$(realpath -m "${OUTPUT}")"

TMPDIR=$(mktemp -d)
trap "rm -rf ${TMPDIR}" EXIT
cd "${TMPDIR}"

# Compile with cpp → cc1 → maspsx → GAS → .o (matches build system)
${CPP} -E -lang-c -nostdinc -I"${DIR}/include" -DPERMUTER "${INPUT_ABS}" -o "out.i"
${CC1} -quiet ${COMPILE_FLAGS} "out.i" -o "out.s"
cat out.s | ${MASPSX} ${ASPSX_FLAGS} --run-assembler \
    ${ASFLAGS} -o "${OUTPUT_ABS}"
COMPILE_EOF

chmod +x "${FUNC_DIR}/compile.sh"

# --- diff.sh ---
# Compiles base.c via compile.sh, then prints a side-by-side asm diff against
# target.o for this function.
cat > "${FUNC_DIR}/diff.sh" <<DIFF_EOF
#!/usr/bin/env bash
# Compile base.c and diff against target.o for ${FUNC_NAME}.
# Usage: ./diff.sh [base.c]   (defaults to ./base.c)
set -euo pipefail
HERE="\$(cd "\$(dirname "\$0")" && pwd)"
PROJECT="${SCRIPT_DIR}"
INPUT="\${1:-\${HERE}/base.c}"
OUT="\${HERE}/current.o"
"\${HERE}/compile.sh" "\${INPUT}" -o "\${OUT}"
exec python3 "\${PROJECT}/tools/diff_func.py" \\
    --target "\${HERE}/target.o" --base "\${OUT}" "${FUNC_NAME}"
DIFF_EOF
chmod +x "${FUNC_DIR}/diff.sh"

# --- target.s ---
# Prepend macro.inc include + .set noreorder (matches INCLUDE_ASM wrapper)
{
    echo '.include "include/macro.inc"'
    echo '.set noreorder'
    echo '.set noat'
    echo ""
    cat "${TARGET_ASM}"
} > "${FUNC_DIR}/target.s"

# --- target.o ---
# Assemble the target so the permuter has a .o to compare against
cd "${SCRIPT_DIR}"
${AS} ${ASFLAGS} -o "${FUNC_DIR}/target.o" "${FUNC_DIR}/target.s"

# --- base.c ---
# Try to extract the function from the source file. If the function isn't
# decomped yet (INCLUDE_ASM or absent), generate an empty stub instead.
HAVE_DECOMP=0
if grep -q "${FUNC_NAME}" "${SRC_FILE}" 2>/dev/null && \
   ! grep -q "INCLUDE_ASM.*${FUNC_NAME}" "${SRC_FILE}" 2>/dev/null; then
    HAVE_DECOMP=1
fi

if [[ "${HAVE_DECOMP}" -eq 1 ]]; then
    ${CPP} -E -lang-c -nostdinc -Iinclude -DPERMUTER "${SRC_FILE}" > "${FUNC_DIR}/base.c.tmp"
    cp "${FUNC_DIR}/base.c.tmp" "${FUNC_DIR}/base.c"
    rm "${FUNC_DIR}/base.c.tmp"
    if [[ -f "${PERMUTER_DIR}/strip_other_fns.py" ]]; then
        python3 "${PERMUTER_DIR}/strip_other_fns.py" "${FUNC_DIR}/base.c" "${FUNC_NAME}"
    fi
    BASE_C_DESC="extracted from source"
else
    cat > "${FUNC_DIR}/base.c" <<BASEC_EOF
void ${FUNC_NAME}(void) {
    // TODO: decompile this function
}
BASEC_EOF
    BASE_C_DESC="empty stub"
fi

echo ""
echo "Permuter directory ready: ${FUNC_DIR}"
echo "  settings.toml  - permuter settings"
echo "  compile.sh     - compilation pipeline"
echo "  diff.sh        - compile base.c and diff vs target.o"
echo "  target.s       - target assembly"
echo "  target.o       - assembled target"
echo "  base.c         - ${BASE_C_DESC}"

# --- Optionally run the permuter ---
if [[ "${RUN}" -eq 1 ]]; then
    echo ""
    echo "Running permuter..."
    python3 "${PERMUTER_DIR}/permuter.py" "${PERMUTER_ARGS[@]}" "${FUNC_DIR}"
fi
