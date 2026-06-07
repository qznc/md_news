#!/usr/bin/env python3
"""Summary validation utilities for md-news."""

from typing import Optional


def is_valid_summary(summary: str, topic: Optional[str] = None) -> bool:
    """Check if summary is valid: non-empty, starts with #, has links, contains --- separator, has both commentaries, and mentions topic."""
    if not summary.strip():
        return False
    if len(summary) < 200:
        return False
    if not summary.lstrip().startswith("# "):
        return False
    if "[" not in summary or "](" not in summary:
        return False
    if "---" not in summary:
        return False
    if "Grumpy's commentary:" not in summary:
        return False
    if "Bubbles's commentary:" not in summary:
        return False
    if summary.count("\n\n") < 2:
        return False
    return True
