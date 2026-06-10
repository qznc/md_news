#!/usr/bin/env python3

import html
import html.parser
import json
import urllib.parse
import urllib.request
from typing import cast
from urllib.error import HTTPError


class _HTMLToText(html.parser.HTMLParser):
    """Convert HN HTML comment text to plain text."""

    # Tags that map to a newline separator
    _BLOCK_TAGS = {"p", "br", "div"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self._block_tags:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._block_tags:
            self._parts.append("\n")

    @property
    def _block_tags(self) -> set[str]:
        return self._BLOCK_TAGS

    def result(self) -> str:
        return "".join(self._parts).strip()


def _html_to_text(raw: str) -> str:
    """Strip HTML tags and unescape entities from HN comment/post text."""
    if not raw:
        return raw
    parser = _HTMLToText()
    parser.feed(raw)
    return parser.result()


_API = "https://hacker-news.firebaseio.com/v0"
_FRONTPAGE_URL = "https://news.ycombinator.com/"


def _item_url(item_id: int) -> str:
    return f"{_API}/item/{item_id}.json"


def _fetch_json(url: str) -> object:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _is_item_url(url: str) -> bool:
    """Return True for URLs like https://news.ycombinator.com/item?id=12345."""
    parsed = urllib.parse.urlparse(url)
    return parsed.path == "/item" and "id=" in (parsed.query or "")


def _fetch_frontpage() -> list[dict]:
    top_ids = cast(list[int], _fetch_json(f"{_API}/topstories.json"))
    posts = []
    for item_id in top_ids[:30]:
        try:
            item = cast(dict, _fetch_json(_item_url(item_id)))
        except HTTPError:
            continue
        posts.append(
            {
                "title": item.get("title", ""),
                "url": item.get(
                    "url", f"https://news.ycombinator.com/item?id={item_id}"
                ),
                "author": item.get("by", ""),
                "score": item.get("score", 0),
                "num_comments": item.get("descendants", 0),
                "item_id": item_id,
            }
        )
    return posts


def _fetch_item(item_id: int) -> list[dict]:
    item = cast(dict, _fetch_json(_item_url(item_id)))
    comments = _fetch_comments(item.get("kids", []), depth=0)
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
            "author": item.get("by", ""),
            "score": item.get("score", 0),
            "selftext": _html_to_text(item.get("text", "")),
            "comments": comments,
            "item_id": item_id,
        }
    ]


def _fetch_comments(kids: list[int], depth: int) -> list[dict]:
    """Fetch top-level comments only to keep things simple."""
    if depth > 0 or not kids:
        return []
    comments = []
    for kid_id in kids[:20]:
        try:
            item = cast(dict, _fetch_json(_item_url(kid_id)))
        except HTTPError:
            continue
        if item.get("deleted") or item.get("dead"):
            continue
        comments.append(
            {
                "author": item.get("by", ""),
                "body": _html_to_text(item.get("text", "")),
                "score": item.get("score", 0),
            }
        )
    return comments


def fetch(url: str) -> str:
    """Fetch a HN page and return it as a Markdown string."""
    if _is_item_url(url):
        parsed = urllib.parse.urlparse(url)
        item_id = int(urllib.parse.parse_qs(parsed.query)["id"][0])
        data = _fetch_item(item_id)
    else:
        # Treat any other HN URL as the frontpage
        data = _fetch_frontpage()

    text = ""
    for post in data:
        text += f"## {post['title']}\n"
        text += f"url: {post['url']}\n"
        if post.get("selftext"):
            text += f"> {post['selftext']}\n"
        for comment in post.get("comments", []):
            text += f"\ncomment by {comment['author']}:\n{comment['body']}\n"
        text += "\n"
    return text


if __name__ == "__main__":
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else _FRONTPAGE_URL
    print(fetch(url))

    # example URLs to try
    # https://news.ycombinator.com/
    # https://news.ycombinator.com/item?id=48477135
