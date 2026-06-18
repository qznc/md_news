#!/usr/bin/env python3
"""
Script to fetch top posts from r/de (German) subreddit.
"""

import time
from typing import Any, Dict

from lib.logging import logger
from lib.reddit_utils import REQUEST_DELAY, get_subreddit_top

# German subreddits - start with r/de
DE_SUBREDDITS = [
    "de",
    "deutschland",
    "Germany",
]


def format_post(post: Dict[str, Any], index: int, subreddit: str) -> str:
    """Format a Reddit post as a string."""
    title = post.get("title", "No title")
    url = post.get("url", "")
    content = post.get("content", "")

    # Rewrite www.reddit.com URLs to old.reddit.com for better lynx parsing
    if "www.reddit.com" in url:
        url = url.replace("www.reddit.com", "old.reddit.com")

    lines = []
    lines.append(f"{index}. {title}")
    lines.append(f"   URL: {url}")
    if content:
        lines.append(f"   Content: {content}")

    return "\n".join(lines) + "\n"


def get_de_subreddits_output(limit: int = 10) -> str:
    """
    API function to fetch and return top posts from German subreddits.

    Args:
        limit: Maximum number of posts to fetch from each subreddit

    Returns:
        Formatted string with top posts from each subreddit
    """
    output_lines = []
    output_lines.append("Top German Reddit Communities - Latest Posts")
    output_lines.append("")

    for subreddit in DE_SUBREDDITS:
        output_lines.append(f"\n--- r/{subreddit} ---")

        try:
            posts = get_subreddit_top(subreddit, limit)

            if not posts:
                output_lines.append(f"No posts found for r/{subreddit}")
                continue

            for i, post in enumerate(posts[:limit], 1):
                output_lines.append(format_post(post, i, subreddit))

        except Exception as e:
            output_lines.append(f"Error fetching r/{subreddit}: {e}")

        # Rate limiting between subreddits to be polite
        time.sleep(REQUEST_DELAY)

    output_lines.append("\n" + "=" * 80)
    output_lines.append(
        f"Fetched top {limit} posts from {len(DE_SUBREDDITS)} German subreddits"
    )
    output_lines.append("=" * 80)

    return "\n".join(output_lines) + "\n"


if __name__ == "__main__":
    output = get_de_subreddits_output(limit=10)
    logger.info(f"Reddit DE output:\n{output}")
    print(output)
