#!/usr/bin/env bash
# Build and package selected variants on a Linux filesystem, including under WSL.
set -e
if [ "$#" -lt 2 ]; then
    echo "Usage: bash build_boards.sh /path/to/board-files 4gb [8gb]" >&2
    exit 2
fi
board_files=$(realpath "$1")
shift
here=$(cd "$(dirname "$0")" && pwd)
build="$here/../build"
ip=${POCKETFILTER_IP_REPO:-"$build/pocketfilter_hls/solution1/impl/ip"}
test -f "$ip/component.xml"
for variant in "$@"; do
    case "$variant" in 4gb|8gb) ;; *) echo "Unknown variant $variant" >&2; exit 2 ;; esac
    test -f "$board_files/aup-zu3-$variant/1.0/board.xml"
done
export POCKETFILTER_VIVADO_WORK=$(mktemp -d)
echo "Vivado project directory: $POCKETFILTER_VIVADO_WORK"
cp -r "$ip" "$POCKETFILTER_VIVADO_WORK/ip"
cp -r "$board_files" "$POCKETFILTER_VIVADO_WORK/board-files"
export POCKETFILTER_IP_REPO="$POCKETFILTER_VIVADO_WORK/ip"
cd "$build"
for variant in "$@"; do
    vivado -mode batch -journal "$variant.jou" -log "$variant.log" \
        -source "$here/build_overlay.tcl" \
        -tclargs "$variant" "$POCKETFILTER_VIVADO_WORK/board-files" bitstream
    # Preserve earlier packages when rerunning.
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    python3 "$here/../pynq/package_overlay.py" "overlay/$variant" "pocketfilter-$variant-$stamp.zip"
done
