#!/usr/bin/env python3
"""Hacker News API utilities for md-news."""

import json
from typing import Any, Dict, List, Optional
from urllib.error import URLError, HTTPError
from urllib.request import urlopen, Request

COMMENT_MAX_LENGTH = 1000


def fetch_top_stories(limit: int = 50) -> List[int]:
    """Fetch the top stories IDs from HN API."""
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    req = Request(url)
    with urlopen(req, timeout=30) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)[:limit]


def fetch_item(item_id: int) -> Dict[str, Any]:
    """Fetch details for a single item (story or comment)."""
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    req = Request(url)
    with urlopen(req, timeout=30) as response:
        data = response.read().decode("utf-8")
        return json.loads(data)


def fetch_story(story_id: int) -> Dict[str, Any]:
    """Fetch details for a single story."""
    return fetch_item(story_id)


def fetch_top_comment(story: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fetch the first top-level comment for a story."""
    kids = story.get("kids", [])
    if not kids:
        return None

    # Take the first kid
    for comment_id in kids:
        try:
            comment = fetch_item(comment_id)
            if comment and not comment.get("deleted") and not comment.get("dead"):
                return comment
        except (URLError, HTTPError, json.JSONDecodeError):
            continue

    return None


def get_frontpage_stories(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch all frontpage stories with their details."""
    story_ids = fetch_top_stories(limit)
    stories = []

    for story_id in story_ids:
        try:
            story = fetch_story(story_id)
            stories.append(story)
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            stories.append({"id": story_id, "error": str(e)})

    return stories
