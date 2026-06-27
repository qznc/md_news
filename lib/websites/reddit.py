#!/usr/bin/env python3

import json
import logging
import re
import time
import urllib.request
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.parse import quote

USER_AGENT = "Lynx/2.9.2 libwww-FM/2.14 SSL-MM/1.4.1"

# Matches post URLs like /r/sub/comments/id/slug/
_POST_RE = re.compile(r"/r/\w+/comments/")

_COOKE_JAR = CookieJar()
_LOG = logging.getLogger(__name__)


def _normalize_url(url: str) -> str:
    """Rewrite to old.reddit.com and ensure no double .json suffix."""
    url = url.replace("www.reddit.com", "old.reddit.com")
    if "old.reddit.com" not in url:
        url = url.replace("reddit.com", "old.reddit.com")
    url = url.rstrip("/")
    if not url.endswith(".json"):
        url += ".json"
    # URL-encode non-ASCII characters, keeping URL-safe characters intact
    return quote(url, safe=":/?#[]@!$&'()*+,;=")


def _html_url(url: str) -> str:
    """Get the HTML page URL (for the cookie-priming request)."""
    url = url.replace("www.reddit.com", "old.reddit.com")
    if "old.reddit.com" not in url:
        url = url.replace("reddit.com", "old.reddit.com")
    url = url.rstrip("/") + "/"
    # URL-encode non-ASCII characters, keeping URL-safe characters intact
    return quote(url, safe=":/?#[]@!$&'()*+,;=")


def _build_opener() -> tuple[urllib.request.OpenerDirector, CookieJar]:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_COOKE_JAR))
    return opener, _COOKE_JAR


def _parse_listing(data: dict) -> list[dict]:
    """Extract posts from a subreddit listing response."""
    children = data.get("data", {}).get("children", [])
    posts = []
    for child in children:
        d = child.get("data", {})
        posts.append(
            {
                "title": d.get("title", ""),
                "url": d.get("url", ""),
                "permalink": "https://old.reddit.com" + d.get("permalink", ""),
                "author": d.get("author", ""),
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "selftext": d.get("selftext", ""),
                "subreddit": d.get("subreddit", ""),
                "created_utc": d.get("created_utc", 0),
            }
        )
    return posts


def _parse_comments(listing: dict) -> list[dict]:
    """Recursively extract comments from a comment listing."""
    comments = []
    for child in listing.get("data", {}).get("children", []):
        if child.get("kind") != "t1":
            continue
        d = child.get("data", {})
        comment: dict = {
            "author": d.get("author", ""),
            "body": d.get("body", ""),
            "score": d.get("score", 0),
        }
        replies = d.get("replies")
        if isinstance(replies, dict):
            comment["replies"] = _parse_comments(replies)
        comments.append(comment)
    return comments


def _parse_post(data: list) -> list[dict]:
    """Parse a post page response (list of two listings: post + comments)."""
    posts = _parse_listing(data[0])
    post = posts[0] if posts else {}

    comments = _parse_comments(data[1])
    post["comments"] = comments
    return [post]


def _fetch(url: str) -> list[dict]:
    """Fetch JSON data from any reddit.com URL.

    For subreddits, returns a list of posts.
    For post URLs, returns a single-element list with the post and its comments.
    """
    json_url = _normalize_url(url)
    html_url = _html_url(url)
    is_post = bool(_POST_RE.search(url))

    opener, _jar = _build_opener()

    # Prime cookies by visiting the HTML page first.
    # Reddit blocks .json requests that don't carry session cookies.
    prime_req = urllib.request.Request(html_url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(prime_req, timeout=30) as resp:
            resp.read()
    except HTTPError:
        pass

    time.sleep(0.1)  # Reddit access is rate-limited!

    req = urllib.request.Request(json_url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(req, timeout=30) as resp:
            data = json.load(resp)
    except HTTPError as e:
        _LOG.error(f"Error fetching {json_url}: {e.code} {e.reason}")
        return []

    time.sleep(0.5)  # Reddit access is rate-limited!

    if is_post and isinstance(data, list):
        return _parse_post(data)
    elif isinstance(data, dict):
        return _parse_listing(data)

    return data


def fetch(url: str) -> str:
    """Fetch the HTML page and return it as a string."""
    data = _fetch(url)
    # serialize to text Markdown-style
    text = ""
    for post in data:
        text += f"## {post['title']}\n"
        text += f"url: {post['url']}\n"
        text += f"> {post['selftext']}\n"
        for comment in post.get("comments", []):
            text += f"\ncomment by {comment['author']}:\n{comment['body']}\n"
        text += "\n"
    return text


if __name__ == "__main__":
    import sys

    url = sys.argv[1]
    result = fetch(url)
    print(result)

    # example URLs to try
    # https://www.reddit.com/r/de/comments/1u2b78o/ich_denke_sie_lebt_nicht_mehr_vermisste_deutsche/
    # https://old.reddit.com/r/de/
    # https://www.reddit.com/r/ollama/
