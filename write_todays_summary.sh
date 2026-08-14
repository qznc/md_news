#!/bin/bash
set -euo pipefail

summarize() {
    BASE_DIR_NAME=$1
    SCRIPT=$2
    OUTPUT_DIR="./_out/$BASE_DIR_NAME/$(date +"%Y")/$(date +"%m")"
    OUTPUT_FILE="$(date +"%d").md"
    TMP_FILE="$OUTPUT_FILE.tmp"

    mkdir -p "$OUTPUT_DIR"
    "./$SCRIPT" > "$OUTPUT_DIR/$TMP_FILE"
    mv -f "$OUTPUT_DIR/$TMP_FILE" "$OUTPUT_DIR/$OUTPUT_FILE" # atomic update
    echo "Output written to: $OUTPUT_DIR/$OUTPUT_FILE" >&2
}

summarize "hn" "hn_summary.py"

# reddit access disabled
#summarize "ai" "ai_summary.py"
#summarize "de" "de_summary.py"

./to_html.py
./gen_index.py
