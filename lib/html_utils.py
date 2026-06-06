#!/usr/bin/env python3
"""Common utilities for HTML generation in md-news."""

from pathlib import Path
from typing import Optional


# Common CSS for all generated HTML pages
COMMON_CSS = """
    body { font-size: 18pt; line-height: 1.6; max-width: 40em; margin: 0 auto; background-color: rgb(246, 246, 239); }
    footer { font-size: 12pt; }
    hr { border: 0; border-top: 1px solid #ccc; margin: 20px 0; }
"""


def get_common_style_tag():
    """Return the style tag with common CSS."""
    return f"<style>{COMMON_CSS}</style>"


def extract_first_headline(markdown_text: str) -> Optional[str]:
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


def extract_title(md_path: Path) -> str:
    """Extract the first heading from a markdown file as the title."""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    return line[2:].strip()
    except Exception:
        pass
    return md_path.stem.replace("-", " ").title()


def html_header(title: str, extra_head: str = "") -> str:
    """Generate the header section of an HTML document."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {get_common_style_tag()}
    {extra_head}
</head>
<body>
"""


def html_footer() -> str:
    """Generate the footer section of an HTML document."""
    return "</body></html>"
