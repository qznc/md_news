#!/usr/bin/env python3
"""Convert all .md files in _out/ to .html files using a basic Markdown compiler.

Supports: headlines (#, ##, ###), paragraphs, links, em, strong, hr (---).
"""

import re
from pathlib import Path


def markdown_to_html(markdown_text):
    """Convert markdown text to HTML with support for headlines, paragraphs, links, em, strong."""
    html_lines = []
    in_list = False
    in_code_block = False

    # Split into lines and process
    lines = markdown_text.split("\n")

    for line in lines:
        # Skip empty lines (handle paragraph breaks)
        if not line.strip():
            # Close any open paragraph if we hit a blank line
            if html_lines and html_lines[-1] == "<p>":
                html_lines.pop()  # Remove the opening <p>
            elif html_lines and html_lines[-1].startswith("<p>"):
                html_lines.append("</p>")
            continue

        # Horizontal rule (---- or ****)
        stripped = line.strip()
        if stripped in ("---", "***", "___"):
            if html_lines and html_lines[-1] == "<p>":
                html_lines.pop()
            elif html_lines and html_lines[-1].startswith("<p>"):
                html_lines.append("</p>")
            html_lines.append("<hr />")
            continue

        # Check for code blocks
        if line.startswith("```"):
            if in_code_block:
                html_lines.append("</pre>")
                in_code_block = False
            else:
                html_lines.append("<pre>")
                in_code_block = True
            continue

        # Code block content
        if in_code_block:
            html_lines.append(line)
            continue

        # Headlines
        if line.startswith("# "):
            if html_lines and html_lines[-1] == "<p>":
                html_lines.pop()
            elif html_lines and html_lines[-1].startswith("<p>"):
                html_lines.append("</p>")
            html_lines.append(f"<h1>{line[2:].strip()}</h1>")
            continue
        elif line.startswith("## "):
            if html_lines and html_lines[-1] == "<p>":
                html_lines.pop()
            elif html_lines and html_lines[-1].startswith("<p>"):
                html_lines.append("</p>")
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
            continue
        elif line.startswith("### "):
            if html_lines and html_lines[-1] == "<p>":
                html_lines.pop()
            elif html_lines and html_lines[-1].startswith("<p>"):
                html_lines.append("</p>")
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
            continue

        # Lists
        if line.startswith("- "):
            if not in_list:
                if html_lines and html_lines[-1] == "<p>":
                    html_lines.pop()
                elif html_lines and html_lines[-1].startswith("<p>"):
                    html_lines.append("</p>")
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:].strip()}</li>")
            continue

        # If we've been in a list but this isn't a list line, close the list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

        # Start a paragraph if not already in one
        if not html_lines or not html_lines[-1].startswith("<p>"):
            if html_lines and html_lines[-1] != "<p>":
                # Close previous non-paragraph element
                pass
            html_lines.append("<p>")

        # Process inline markdown within the line
        processed_line = process_inline_markdown(line)
        html_lines.append(processed_line)

    # Close any open tags at the end
    if in_code_block:
        html_lines.append("</pre>")
    if in_list:
        html_lines.append("</ul>")
    if html_lines and html_lines[-1] == "<p>":
        html_lines.pop()  # Remove unclosed <p>
    elif html_lines and html_lines[-1].startswith("<p>"):
        html_lines.append("</p>")

    return "\n".join(html_lines)


def extract_first_headline(markdown_text):
    """Extract the first headline from markdown text."""
    lines = markdown_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        elif stripped.startswith("## "):
            return stripped[3:].strip()
        elif stripped.startswith("### "):
            return stripped[4:].strip()
        elif stripped.startswith("#### "):
            return stripped[5:].strip()
        elif stripped.startswith("##### "):
            return stripped[6:].strip()
        elif stripped.startswith("###### "):
            return stripped[7:].strip()
    return None


def process_inline_markdown(text):
    """Process inline markdown: links, em, strong."""
    # Process **strong** first
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)

    # Process *em*
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)

    # Process links [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)

    return text


def process_file(md_path, out_dir):
    """Process a single markdown file and create its HTML counterpart."""
    html_path = md_path.with_suffix(".html")

    # Skip if HTML file already exists
    if html_path.exists():
        print(f"Skipped (already exists): {html_path}")
        return

    # Read the markdown file
    with open(md_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    # Extract first headline for title
    title = extract_first_headline(markdown_content)
    if title is None:
        title = Path(md_path).stem

    # Convert to HTML
    html_content = markdown_to_html(markdown_content)

    # Create HTML wrapper
    md_stem = Path(md_path).stem
    md_relative = md_path.name
    html_wrapper = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="canonical" href="{md_relative}">
    <link rel="alternate" type="text/markdown" href="{md_relative}" title="Original Markdown source">
    <style>
        body {{ font-size: 18pt; line-height: 1.6; max-width: 40em; margin: 0 auto; }}
        footer {{ font-size: 12pt; }}
        hr {{ border: 0; border-top: 1px solid #ccc; margin: 20px 0; }}
    </style>
</head><body>
{html_content}
<footer>Markdown original: <a href="{md_relative}">{md_relative}</a></footer>
</body></html>
"""

    # Write HTML file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_wrapper)

    print(f"Converted: {md_path} -> {html_path}")


def main():
    """Find all .md files in _out/ and convert them to .html."""
    out_dir = Path("_out")

    if not out_dir.exists():
        print(f"Directory '{out_dir}' does not exist.")
        return

    # Find all .md files recursively
    md_files = list(out_dir.rglob("*.md"))

    if not md_files:
        print("No .md files found in _out/")
        return

    print(f"Found {len(md_files)} .md file(s) to convert")

    for md_file in md_files:
        process_file(md_file, out_dir)

    print("Done!")


if __name__ == "__main__":
    main()
