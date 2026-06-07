#!/bin/bash

# HN Summary
OUTPUT_DIR="_out/hn/$(date +"%Y")/$(date +"%m")"
OUTPUT_FILE="$(date +"%d").md"

mkdir -p "$OUTPUT_DIR"
./hn_summary.py > "$OUTPUT_DIR/$OUTPUT_FILE"
echo "HN Output written to: $OUTPUT_DIR/$OUTPUT_FILE" >&2

# AI Summary
AI_OUTPUT_DIR="_out/ai/$(date +"%Y")/$(date +"%m")"
AI_OUTPUT_FILE="$(date +"%d").md"

mkdir -p "$AI_OUTPUT_DIR"
./ai_summary.py > "$AI_OUTPUT_DIR/$AI_OUTPUT_FILE"
echo "AI Output written to: $AI_OUTPUT_DIR/$AI_OUTPUT_FILE" >&2

./to_html.py
./gen_index.py
