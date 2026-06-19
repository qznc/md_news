#!/usr/bin/env python3
"""Convert all .md files in _out/ to .html files using a basic Markdown compiler.

Supports: headlines (#, ##, ###), paragraphs, links, em, strong, hr (---).
"""

from pathlib import Path

from lib.html_utils import extract_first_headline, html_footer, html_header
from lib.logging import logger
from lib.markdown import markdown_to_html


def process_file(md_path, out_dir):
    """Process a single markdown file and create its HTML counterpart."""
    html_path = md_path.with_suffix(".html")

    # Skip if HTML file already exists and is up-to-date
    if html_path.exists() and html_path.stat().st_mtime >= md_path.stat().st_mtime:
        logger.debug(f"Skipped (already exists and up-to-date): {html_path}")
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
    md_relative = md_path.name
    extra_head = f'\n    <link rel="canonical" href="{md_relative}">\n    <link rel="alternate" type="text/markdown" href="{md_relative}" title="Original Markdown source">'
    html_wrapper = f"""{html_header(title, extra_head)}
{html_content}
<footer>Markdown original: <a href="{md_relative}">{md_relative}</a>, <a href="../../index.html">index</a></footer>
{html_footer()}
"""

    # Write HTML file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_wrapper)

    logger.info(f"Converted: {md_path} -> {html_path}")


def main():
    """Find all .md files in _out/ and convert them to .html."""
    out_dir = Path("_out")

    if not out_dir.exists():
        logger.info(f"Directory '{out_dir}' does not exist.")
        return

    # Find all .md files recursively
    md_files = list(out_dir.rglob("*.md"))

    if not md_files:
        logger.info("No .md files found in _out/")
        return

    logger.info(f"Found {len(md_files)} .md file(s) to convert")

    for md_file in md_files:
        process_file(md_file, out_dir)

    logger.info("Done!")


if __name__ == "__main__":
    main()
