"""Web utilities for md-news."""

import subprocess
import urllib.request
from typing import Optional
from urllib.error import HTTPError

from lib.logging import logger
from lib.websites import hackernews, reddit

MAX_LINES = 300

# Not avoid re-fetching on second attempts
_CACHE = {}


def _fetch_url_content1(url: str, max_lines: Optional[int] = None) -> str:
    """Fetch via urllib2, limited to max_lines lines."""

    if max_lines is None:
        max_lines = MAX_LINES

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
        max_lines: Maximum number of lines to return

    Returns:
        The fetched content as a string, or an error message if fetching fails.
    """
    if max_lines is None:
        max_lines = MAX_LINES

    result = subprocess.run(
        ["lynx", "-dump", "-list_inline", url],
        capture_output=True,
        text=True,
        timeout=60,
        errors="replace",
    )
    if result.returncode != 0:
        logger.warning(
            f"lynx returned {result.returncode} for {url}. stderr: {result.stderr}"
        )
        raise HTTPError(url, result.returncode, "lynx error", None, None)
    lines = result.stdout.splitlines()
    return "\n".join(lines[:max_lines])


def _is_reddit(url: str) -> bool:
    from urllib.parse import urlparse

    host = urlparse(url).netloc
    return host == "reddit.com" or host.endswith(".reddit.com")


def _is_hackernews(url: str) -> bool:
    from urllib.parse import urlparse

    host = urlparse(url).netloc
    return host in ("news.ycombinator.com", "ycombinator.com")


def fetch_urls(urls: list[str]) -> dict[str, str]:
    ret = {}
    for url in urls:
        if " " in url:
            i = url.index(" ")
            url = url[:i]
        content = _CACHE.get(url, None)
        if not content:
            logger.info(f"Fetching: {url}")
            try:
                if _is_reddit(url):
                    content = reddit.fetch(url)
                elif _is_hackernews(url):
                    content = hackernews.fetch(url)
                else:
                    content = _fetch_url_content2(url)
                _CACHE[url] = content
                ret[url] = content
            except HTTPError as e:
                logger.debug(f"Skipping {url} cause {e}")
                continue
    return ret
