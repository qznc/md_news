#!/usr/bin/env python3
"""
Script to fetch Hacker News frontpage and report:
- Top 3 articles
- Most commented article
- Most upvoted article
"""

import json
from typing import Any, Dict, List, Optional

import requests

COMMENT_MAX_LENGTH = 1000


def fetch_top_stories(limit: int = 50) -> List[int]:
    """Fetch the top stories IDs from HN API."""
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()[:limit]


def fetch_item(item_id: int) -> Dict[str, Any]:
    """Fetch details for a single item (story or comment)."""
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


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
        except (requests.RequestException, json.JSONDecodeError):
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
        except (requests.RequestException, json.JSONDecodeError) as e:
            stories.append({"id": story_id, "error": str(e)})

    return stories


def format_story(
    story: Dict[str, Any],
    index: Optional[int] = None,
    top_comment: Optional[Dict[str, Any]] = None,
) -> str:
    """Format a story as a string, optionally with its top comment."""
    prefix = f"{index}. " if index is not None else ""
    title = story.get("title", "No title")
    url = story.get("url", "No URL")
    story_id = story.get("id", "")
    score = story.get("score", 0)
    comments = story.get("descendants", 0)
    author = story.get("by", "Anonymous")

    lines = []
    lines.append(f"{prefix}{title}")
    lines.append(f"   URL: {url}")
    lines.append(f"   HN: https://news.ycombinator.com/item?id={story_id}")
    lines.append(f"   Score: {score} | Comments: {comments} | By: {author}")

    if top_comment:
        comment_text = top_comment.get("text", "No text")
        comment_author = top_comment.get("by", "Anonymous")
        # Truncate long comments
        if len(comment_text) > COMMENT_MAX_LENGTH:
            comment_text = comment_text[:COMMENT_MAX_LENGTH] + "..."
        lines.append(f"   Top comment by {comment_author}:")
        lines.append(f"   {comment_text}")

    return "\n".join(lines) + "\n"


def get_frontpage_output(limit: int = 30) -> str:
    """
    API function to fetch and return HN frontpage data as a formatted string.
    """
    output_lines = []

    try:
        stories = get_frontpage_stories(limit=limit)
    except requests.RequestException as e:
        return f"Error fetching stories: {e}"

    if not stories:
        return "No stories found!"

    # Filter out stories with errors
    valid_stories = [s for s in stories if not s.get("error")]

    if not valid_stories:
        return "No stories found!"

    output_lines.append("Top 3:")
    top_3 = valid_stories[:3]
    for i, story in enumerate(top_3, 1):
        top_comment = fetch_top_comment(story)
        output_lines.append(format_story(story, i, top_comment))

    # Other stories (4-50) as titles only
    other_stories = valid_stories[3:]
    output_lines.append("Other stories:")
    for story in other_stories:
        title = story.get("title", None)
        url = story.get("url", "")
        if title:
            output_lines.append(f"   {title} ({url})")
    output_lines.append("")

    most_commented = max(valid_stories, key=lambda s: s.get("descendants", 0))
    output_lines.append("Most commented:")
    output_lines.append(f"Comments: {most_commented.get('descendants', 0)}")
    top_comment = fetch_top_comment(most_commented)
    output_lines.append(format_story(most_commented, top_comment=top_comment))

    most_upvoted = max(valid_stories, key=lambda s: s.get("score", 0))
    output_lines.append("Most upvoted:")
    output_lines.append(f"Score: {most_upvoted.get('score', 0)}")
    top_comment = fetch_top_comment(most_upvoted)
    output_lines.append(format_story(most_upvoted, top_comment=top_comment))

    return "\n".join(output_lines) + "\n"


if __name__ == "__main__":
    output = get_frontpage_output(limit=30)
    print(output)
