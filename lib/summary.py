#!/usr/bin/env python3
"""Summary validation utilities for md-news."""

import json
import re
from typing import Dict, List, Optional

from lib.llm import run_llm
from lib.logging import logger
from lib.web import fetch_url_contents


def format_url_contents(urls_dict: Dict[str, str]) -> str:
    """Format URL contents dict into the string format expected by generate_summary.

    Args:
        urls_dict: Dict mapping URLs to their fetched content

    Returns:
        Formatted string in the format "URL: {url}\nContent:\n{content}\n\n" for each URL
    """
    url_contents = []
    for url, content in urls_dict.items():
        url_contents.append(f"URL: {url}\nContent:\n{content}")
    return "\n\n".join(url_contents)


def select_topic_and_urls(
    select_prompt_template: str, posts_text: str, tmp_dir: str
) -> Dict[str, object]:
    """Use LLM to select a topic and URLs from posts.

    Args:
        select_prompt_template: The template string for the selection prompt
        posts_text: The text of posts to analyze
        tmp_dir: Temporary directory for debugging files

    Retries up to 3 times if the response is invalid.
    Failed URLs are filtered out as long as at least 3 successful URLs remain.
    Returns a dict with 'topic' and 'urls' keys, where 'urls' is a dict mapping
    URLs to their fetched content.

    Raises:
        RuntimeError: If all attempts fail or if fewer than 3 URLs can be fetched.
    """

    select_prompt = select_prompt_template.format(posts_text=posts_text)

    for attempt in range(1, 4):
        logger.info(f"Step 1 attempt {attempt}/3")
        with open(f"{tmp_dir}/_1_select_prompt.txt", "w") as f:
            f.write(select_prompt)
        select_response = run_llm(select_prompt)
        with open(f"{tmp_dir}/_2_select_response.txt", "w") as f:
            f.write(select_response)

        json_match = re.search(r"\{[^\}]*\}", select_response, re.DOTALL)
        if not json_match:
            logger.error(
                f"Could not find JSON in LLM response on attempt {attempt}. Response was: {select_response}"
            )
            continue

        try:
            selection = json.loads(json_match.group(0))
            topic = selection.get("topic", "Untitled Topic")
            urls = selection.get("urls", [])
        except json.JSONDecodeError as e:
            logger.error(
                f"Error parsing JSON on attempt {attempt}: {e}. Response was: {select_response}"
            )
            continue

        if not urls:
            logger.error(f"No URLs selected by LLM on attempt {attempt}")
            continue

        # Fetch and filter URLs - keep successful ones
        urls_text = fetch_url_contents(urls)
        url_contents_dict = {}

        for url_block in urls_text.split("\n\n"):
            if not url_block.startswith("URL: "):
                continue
            # Parse the URL and content
            parts = url_block.split("\nContent:", 1)
            if len(parts) == 2:
                url_line = parts[0]
                url = url_line[5:]  # Remove "URL: " prefix
                content = parts[1]

                # Check for error messages or empty content - filter out failed URLs
                if (
                    "Error fetching" in content
                    or "Timeout fetching" in content
                    or "lynx not found" in content
                    or not content.strip()
                    or len(content.strip()) < 50  # Too short to be meaningful
                ):
                    logger.warning(
                        f"URL failed to load or has empty content, filtering out: {url}"
                    )
                    continue
                else:
                    url_contents_dict[url] = content

        # If we have at least 3 successful URLs, return the result
        if len(url_contents_dict) >= 3:
            return {"topic": topic, "urls": url_contents_dict}
        else:
            logger.error(
                f"Fewer than 3 URLs succeeded (got {len(url_contents_dict)}) on attempt {attempt}"
            )
            continue

    raise RuntimeError(
        "Failed to select topic and URLs with at least 3 fetchable URLs after 3 attempts"
    )


def is_valid_summary(summary: str, topic: Optional[str] = None) -> bool:
    """Check if summary is valid: non-empty, starts with #, has links, contains --- separator, has both commentaries, and mentions topic."""
    if not summary.strip():
        return False
    if len(summary) < 200:
        return False
    if not summary.lstrip().startswith("# "):
        return False
    if "[" not in summary or "](" not in summary:
        return False
    if "---" not in summary:
        return False
    if "Grumpy's commentary:" not in summary:
        return False
    if "Bubbles's commentary:" not in summary:
        return False
    if summary.count("\n\n") < 2:
        return False
    return True


def generate_summary(
    summary_prompt_template: str,
    tmp_dir: str,
    topic: str,
    urls_text: str,
    thinking: bool = True,
) -> str:
    """Generate the final summary article using the LLM.

    Args:
        summary_prompt_template: The template string for the summary prompt
        tmp_dir: Temporary directory for debugging files
        topic: The topic for the summary
        urls_text: Formatted URL contents
        thinking: Whether to enable reasoning effort (default: True for ai_summary)

    Retries up to 3 times if the summary is invalid.
    """
    summary_prompt = summary_prompt_template.format(topic=topic, url_contents=urls_text)

    for attempt in range(1, 4):
        logger.info(f"Step 2 attempt {attempt}/3")
        with open(f"{tmp_dir}/_3_summary_prompt.txt", "w") as f:
            f.write(summary_prompt)
        summary = run_llm(summary_prompt, thinking=thinking)
        if is_valid_summary(summary, topic):
            return summary
        logger.error(f"Invalid summary on attempt {attempt}")

        if attempt < 3:
            appendix = "\n\n(This is attempt {attempt}. The previous summary was invalid. Try harder!)"
            summary_prompt += appendix.format(attempt=attempt + 1)

    return ""
