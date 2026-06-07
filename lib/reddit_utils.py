#!/usr/bin/env python3
"""Reddit utilities for md-news."""

import time
from typing import Any, Dict, List
from urllib.error import URLError, HTTPError
from urllib.request import urlopen, Request

FEED_BASE = "https://www.reddit.com"

# Rate limiting: be polite even with RSS
REQUEST_DELAY = 2.0
MAX_RETRIES = 3


class RedditFeedError(Exception):
    """Custom error for Reddit feed issues."""

    pass


def _fetch_url(url: str, timeout: int = 30) -> str:
    """Fetch URL content with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            req = Request(url, headers={"User-Agent": "md-news/1.0"})
            with urlopen(req, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except (URLError, HTTPError):
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2**attempt)
    raise RedditFeedError("Max retries exceeded")


def _parse_rss_feed(xml_content: str) -> List[Dict[str, Any]]:
    """Parse Reddit RSS feed into a list of story dicts."""
    import xml.etree.ElementTree as ET
    import html

    namespaces = {
        "atom": "http://www.w3.org/2005/Atom",
        "media": "http://search.yahoo.com/mrss/",
    }

    root = ET.fromstring(xml_content)
    entries = []

    for entry in root.findall(".//atom:entry", namespaces):
        story: Dict[str, Any] = {
            "title": "",
            "url": "",
            "id": "",
            "author": "",
            "published": "",
            "subreddit": "",
            "comments_url": "",
            "content": "",
        }

        # Title
        title = entry.find("atom:title", namespaces)
        if title is not None:
            story["title"] = title.text or ""

        # Main URL (first link found - Reddit RSS only has one link per entry)
        for link in entry.findall("atom:link", namespaces):
            if "href" in link.attrib:
                url = link.attrib["href"]
                # Rewrite www.reddit.com URLs to old.reddit.com for better lynx parsing
                if "www.reddit.com" in url:
                    url = url.replace("www.reddit.com", "old.reddit.com")
                story["url"] = url
                story["comments_url"] = url  # Reddit link IS the comments URL
                break

        # Post ID
        entry_id = entry.find("atom:id", namespaces)
        if entry_id is not None:
            story["id"] = entry_id.text or ""

        # Author
        author = entry.find("atom:author/atom:name", namespaces)
        if author is not None:
            # Strip /u/ prefix if present
            author_text = (author.text or "").strip()
            if author_text.startswith("/u/"):
                story["author"] = author_text[3:]
            else:
                story["author"] = author_text

        # Published timestamp
        published = entry.find("atom:published", namespaces)
        if published is not None:
            story["published"] = published.text or ""

        # Subreddit (from category tag - most reliable)
        category = entry.find("atom:category", namespaces)
        if category is not None:
            story["subreddit"] = category.attrib.get("term", "")

        # Fallback: extract from url
        if not story["subreddit"] and story["url"]:
            parts = story["url"].split("/")
            if (
                len(parts) >= 4
                and parts[2] in ("www.reddit.com", "old.reddit.com")
                and len(parts) >= 5
                and parts[3].startswith("r/")
            ):
                story["subreddit"] = parts[3][2:]  # Remove 'r/' prefix

        # Content
        content = entry.find("atom:content", namespaces)
        if content is not None and content.text:
            story["content"] = html.unescape(content.text)

        entries.append(story)

    return entries


def get_feed(subreddit: str = "", sort_by: str = "hot") -> List[Dict[str, Any]]:
    """
    Get stories from a Reddit RSS feed.

    Args:
        subreddit: Subreddit name (e.g., "technology"). Empty for frontpage.
        sort_by: One of: hot, new, top, rising (default: hot)

    Returns:
        List of story dicts with title, url, author, id, published, etc.
    """
    if subreddit:
        url = f"{FEED_BASE}/r/{subreddit}/{sort_by}/.rss"
    else:
        url = f"{FEED_BASE}/{sort_by}/.rss"

    xml_content = _fetch_url(url)
    return _parse_rss_feed(xml_content)


def get_subreddit_top(subreddit: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top stories from a subreddit via RSS.

    Args:
        subreddit: Subreddit name (e.g., "technology")
        limit: Maximum number of stories to return

    Returns:
        List of story dicts
    """
    stories = get_feed(subreddit, "top")
    return stories[:limit]


def get_frontpage_stories(limit: int = 30) -> List[Dict[str, Any]]:
    """Get Reddit frontpage stories via RSS."""
    stories = get_feed("", "hot")
    return stories[:limit]
