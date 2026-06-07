#!/bin/bash

OUTPUT_DIR="_out/hn/$(date +"%Y")/$(date +"%m")"
OUTPUT_FILE="$(date +"%d").md"

mkdir -p "$OUTPUT_DIR"
./hn_summary.py > "$OUTPUT_DIR/$OUTPUT_FILE"
echo "Output written to: $OUTPUT_DIR/$OUTPUT_FILE" >&2

./to_html.py
./gen_index.py
