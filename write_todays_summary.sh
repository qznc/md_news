#!/bin/bash
# Run hn_summary.py and save output to YYYY-MM/DD-hn.md

OUTPUT_DIR="_out/$(date +"%Y-%m")"
OUTPUT_FILE="$(date +"%d")-hn.md"

mkdir -p "$OUTPUT_DIR"
./hn_summary.py > "$OUTPUT_DIR/$OUTPUT_FILE"
echo "Output written to: $OUTPUT_DIR/$OUTPUT_FILE" >&2
