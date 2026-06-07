#!/usr/bin/env python3
"""Web utilities for md-news."""

import subprocess
from typing import Optional


def fetch_url_content(url: str, max_lines: Optional[int] = None) -> str:
    """Fetch URL content using lynx -dump, limited to max_lines lines.
    
    Args:
        url: The URL to fetch
        max_lines: Maximum number of lines to return (default: 200)
    
    Returns:
        The fetched content as a string, or an error message if fetching fails.
    """
    if max_lines is None:
        max_lines = 200
    
    try:
        result = subprocess.run(
            ["lynx", "-dump", "-list_inline", url],
            capture_output=True,
            text=True,
            timeout=60,
            errors="replace",
        )
        if result.returncode != 0:
            return f"Error fetching {url}: {result.stderr}"
        lines = result.stdout.splitlines()
        return "\n".join(lines[:max_lines])
    except subprocess.TimeoutExpired:
        return f"Timeout fetching {url}"
    except FileNotFoundError:
        return f"Error: lynx not found. Cannot fetch {url}"
