#!/usr/bin/env python3
"""
Script to fetch Hacker News frontpage and report:
- Top 3 articles
- Most commented article
- Most upvoted article
"""

from typing import Any, Dict, Optional

from lib.hn_utils import (
    COMMENT_MAX_LENGTH,
    fetch_top_comment,
    get_frontpage_stories,
)


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
    except Exception as e:
        return f"Error fetching stories: {e}"

    if not stories:
        return "No stories found!"

    # Filter out stories with errors
    valid_stories = [s for s in stories if not s.get("error")]

    if not valid_stories:
        return "No stories found!"

    most_upvoted = max(valid_stories, key=lambda s: s.get("score", 0))
    output_lines.append("Most upvoted:")
    output_lines.append(f"Score: {most_upvoted.get('score', 0)}")
    top_comment = fetch_top_comment(most_upvoted)
    output_lines.append(format_story(most_upvoted, top_comment=top_comment))

    most_commented = max(valid_stories, key=lambda s: s.get("descendants", 0))
    output_lines.append("Most commented:")
    output_lines.append(f"Comments: {most_commented.get('descendants', 0)}")
    top_comment = fetch_top_comment(most_commented)
    output_lines.append(format_story(most_commented, top_comment=top_comment))

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
            output_lines.append(f"   {title} {url}")
    output_lines.append("")

    return "\n".join(output_lines) + "\n"


if __name__ == "__main__":
    output = get_frontpage_output(limit=30)
    print(output)
