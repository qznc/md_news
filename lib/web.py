#!/usr/bin/env python3
"""Web utilities for md-news."""

import subprocess
import urllib.request
from typing import Optional
from urllib.error import HTTPError

from lib.logging import logger


def _fetch_url_content1(url: str, max_lines: Optional[int] = None) -> str:
    """Fetch via urllib2, limited to max_lines lines."""

    if max_lines is None:
        max_lines = 200

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    headers = {"User-Agent": user_agent}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        content_bytes = response.read()
        logger.debug(f"Fetched {len(content_bytes)} bytes from {url}")
        content = content_bytes.decode("utf-8", errors="replace")
        lines = content.splitlines()
        return "\n".join(lines[:max_lines])


def _fetch_url_content2(url: str, max_lines: Optional[int] = None) -> str:
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


def fetch_url_contents(urls: list[str]) -> str:
    """Fetch content from all URLs and format them for prompts.

    Args:
        urls: List of URLs to fetch

    Returns:
        A concatenated string of all URL contents formatted as:
        "URL: {url}\nContent:\n{content}\n\n" for each URL
    """
    url_contents = []
    for url in urls:
        logger.info(f"Fetching: {url}")
        try:
            content = _fetch_url_content2(url)
        except HTTPError as e:
            logger.debug(f"Skipping {url} cause {e}")
            continue
        url_contents.append(f"URL: {url}\nContent:\n{content}\n")

    return "\n\n".join(url_contents)
