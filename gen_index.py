#!/usr/bin/env python3
"""Generate index.html for _out/ directory listing all articles with md and html links."""

import re
from pathlib import Path

from lib.html_utils import extract_title, html_header, html_footer

OUT_DIR = Path("_out")
TITLE = "Md News"


def extract_date_from_path(file_path: Path) -> str:
    """Extract date from path like 2026-06/05-hn.md -> 2026-06-05."""
    parts = file_path.parts
    for part in parts:
        if re.match(r"^\d{4}-\d{2}$", part):
            filename = file_path.name
            if match := re.match(r"^(\d{2})-", filename):
                return f"{part}-{match.group(1)}"
            return part
    return ""


def find_articles(out_dir: Path):
    """Find all .md files, assuming corresponding .html files exist."""
    articles = []
    for md_path in out_dir.rglob("*.md"):
        if md_path.name == "gen_index.py":
            continue
        rel_path = md_path.relative_to(out_dir)
        title = extract_title(md_path)
        date_str = extract_date_from_path(md_path)
        articles.append((rel_path, title, date_str))
    return sorted(articles, key=lambda x: (x[2] or "", str(x[0])), reverse=True)


def generate_html_index(articles):
    """Generate the HTML content for the index page."""
    items = []
    for rel_path, title, _ in articles:
        dir_part = str(rel_path.parent) if rel_path.parent != Path(".") else "."
        md_name = rel_path.name
        html_name = rel_path.with_suffix(".html").name
        md_href = f"{dir_part}/{md_name}" if dir_part != "." else md_name
        html_href = f"{dir_part}/{html_name}" if dir_part != "." else html_name
        items.append(
            f'<li><a href="{html_href}">{title}</a> (<a href="{md_href}">{md_href}</a>)</li>'
        )

    items_list = "\n        ".join(items)
    return f"""{html_header(TITLE)}
    <h1>{TITLE}</h1>
    <ul>
        {items_list}
    </ul>
{html_footer()}
"""


def main():
    print(f"Scanning for articles in {OUT_DIR}...")
    articles = find_articles(OUT_DIR)
    print(f"Found {len(articles)} article(s)")
    with open(OUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(generate_html_index(articles))
    print("Done!")


if __name__ == "__main__":
    main()
