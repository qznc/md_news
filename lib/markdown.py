"""Markdown to HTML conversion utilities for md-news."""

import re


def markdown_to_html(markdown_text):
    """Convert markdown text to HTML with support for headlines, paragraphs, links, em, strong."""
    html_paragraphs = []

    paragraphs = markdown_text.split("\n\n")
    for p in paragraphs:
        # Horizontal rule (---- or ****)
        stripped = p.strip()
        if stripped in ("---", "***", "___"):
            html_paragraphs.append("<hr />")
            continue

        # Headlines
        if p.startswith("# "):
            if html_paragraphs and html_paragraphs[-1] == "<p>":
                html_paragraphs.pop()
            elif html_paragraphs and html_paragraphs[-1].startswith("<p>"):
                html_paragraphs.append("</p>")
            html_paragraphs.append(f"<h1>{p[2:].strip()}</h1>")
            continue
        elif p.startswith("## "):
            if html_paragraphs and html_paragraphs[-1] == "<p>":
                html_paragraphs.pop()
            elif html_paragraphs and html_paragraphs[-1].startswith("<p>"):
                html_paragraphs.append("</p>")
            html_paragraphs.append(f"<h2>{p[3:].strip()}</h2>")
            continue
        elif p.startswith("### "):
            if html_paragraphs and html_paragraphs[-1] == "<p>":
                html_paragraphs.pop()
            elif html_paragraphs and html_paragraphs[-1].startswith("<p>"):
                html_paragraphs.append("</p>")
            html_paragraphs.append(f"<h3>{p[4:].strip()}</h3>")
            continue

        # Lists
        is_ul = p.startswith("- ") or p.startswith("* ")
        is_ol = bool(re.match(r"^\d+\.\s+", p))

        if is_ul or is_ol:
            tag = "ul" if is_ul else "ol"
            html_paragraphs.append(f"<{tag}>")

            list_items = []
            current_item = []

            for line in p.split("\n"):
                if not line.strip():
                    continue

                ul_match = re.match(r"^[-*]\s+(.*)", line)
                ol_match = re.match(r"^\d+\.\s+(.*)", line)

                match = ul_match if is_ul else ol_match
                if match:
                    if current_item:
                        list_items.append(" ".join(current_item))
                    current_item = [match.group(1).strip()]
                else:
                    if current_item:
                        current_item.append(line.strip())

            if current_item:
                list_items.append(" ".join(current_item))

            for item in list_items:
                li_text = process_inline_markdown(item)
                html_paragraphs.append(f"<li>{li_text}</li>")

            html_paragraphs.append(f"</{tag}>")
            continue

        # Process inline markdown within the line
        processed_p = process_inline_markdown(p)
        html_paragraphs.append(f"<p>{processed_p}</p>")

    return "\n\n".join(html_paragraphs)


def process_inline_markdown(text):
    """Process inline markdown: links, em, strong."""
    # Process **strong** first
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)

    # Process *em*
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)

    # Process *tt*
    text = re.sub(r"`(.*?)`", r"<tt>\1</tt>", text)

    # Process links [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)

    return text
