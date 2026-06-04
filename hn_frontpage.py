#!/usr/bin/env python3
"""
Script to fetch Hacker News frontpage and report:
- Top 3 articles
- Most commented article
- Most upvoted article
"""

import requests
import json
from typing import List, Dict, Any

# Configuration
COMMENT_MAX_LENGTH = 500


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


def fetch_top_comment(story: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch the first top-level comment for a story."""
    kids = story.get('kids', [])
    if not kids:
        return None
    
    # Take the first kid
    for comment_id in kids:
        try:
            comment = fetch_item(comment_id)
            if comment and not comment.get('deleted') and not comment.get('dead'):
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
            print(f"Warning: Could not fetch story {story_id}: {e}")
            continue
    
    return stories


def print_story(story: Dict[str, Any], index: int = None, top_comment: Dict[str, Any] = None) -> None:
    """Print a story in a formatted way, optionally with its top comment."""
    prefix = f"{index}. " if index is not None else ""
    title = story.get('title', 'No title')
    url = story.get('url', 'No URL')
    score = story.get('score', 0)
    comments = story.get('descendants', 0)
    author = story.get('by', 'Anonymous')
    
    print(f"{prefix}{title}")
    print(f"   URL: {url}")
    print(f"   Score: {score} | Comments: {comments} | By: {author}")
    
    if top_comment:
        comment_text = top_comment.get('text', 'No text')
        comment_author = top_comment.get('by', 'Anonymous')
        # Truncate long comments
        if len(comment_text) > COMMENT_MAX_LENGTH:
            comment_text = comment_text[:COMMENT_MAX_LENGTH] + "..."
        print(f"   Top comment by {comment_author}:")
        print(f"   {comment_text}")
    print()


def main():
    """Main function to fetch and display HN frontpage data."""
    # Fetch stories
    try:
        stories = get_frontpage_stories(limit=50)
    except requests.RequestException as e:
        print(f"Error fetching stories: {e}")
        return
    
    if not stories:
        print("No stories found!")
        return
    
    # Top 3 articles
    print("Top 3:")
    top_3 = stories[:3]
    for i, story in enumerate(top_3, 1):
        top_comment = fetch_top_comment(story)
        print_story(story, i, top_comment)
    
    # Most commented article
    most_commented = max(stories, key=lambda s: s.get('descendants', 0))
    print("Most commented:")
    print(f"Comments: {most_commented.get('descendants', 0)}")
    top_comment = fetch_top_comment(most_commented)
    print_story(most_commented, top_comment=top_comment)
    
    # Most upvoted article
    most_upvoted = max(stories, key=lambda s: s.get('score', 0))
    print("Most upvoted:")
    print(f"Score: {most_upvoted.get('score', 0)}")
    top_comment = fetch_top_comment(most_upvoted)
    print_story(most_upvoted, top_comment=top_comment)


if __name__ == "__main__":
    main()
