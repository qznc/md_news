#!/usr/bin/env python3
"""Markdown to HTML conversion utilities for md-news."""

import re


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


def process_inline_markdown(text):
    """Process inline markdown: links, em, strong."""
    # Process **strong** first
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)

    # Process *em*
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)

    # Process links [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', text)

    return text
