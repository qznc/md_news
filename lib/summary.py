#!/usr/bin/env python3
"""Summary validation utilities for md-news."""

import json
import re
import sys
from typing import List, Optional, Tuple

from lib.llm import run_llm
from lib.logging import logger


def select_topic_and_urls(
    select_prompt_template: str, posts_text: str, tmp_dir: str
) -> Tuple[Optional[str], List[str]]:
    """Use LLM to select a topic and URLs from posts.

    Args:
        select_prompt_template: The template string for the selection prompt
        posts_text: The text of posts to analyze
        tmp_dir: Temporary directory for debugging files

    Retries up to 3 times if the response is invalid.
    Returns (topic, urls) tuple.
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
            logger.error(f"Could not find JSON in LLM response on attempt {attempt}. Response was: {select_response}")
            continue

        try:
            selection = json.loads(json_match.group(0))
            topic = selection.get("topic", "Untitled Topic")
            urls = selection.get("urls", [])
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON on attempt {attempt}: {e}. Response was: {select_response}")
            continue

        if urls:
            return topic, urls
        else:
            logger.error(f"No URLs selected by LLM on attempt {attempt}")

    return None, []


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
) -> str:
    """Generate the final summary article using the LLM.

    Args:
        summary_prompt_template: The template string for the summary prompt
        tmp_dir: Temporary directory for debugging files
        topic: The topic for the summary
        urls_text: Formatted URL contents

    Retries up to 3 times if the summary is invalid.
    """
    summary_prompt = summary_prompt_template.format(topic=topic, url_contents=urls_text)

    for attempt in range(1, 4):
        logger.info(f"Step 2 attempt {attempt}/3")
        with open(f"{tmp_dir}/_3_summary_prompt.txt", "w") as f:
            f.write(summary_prompt)
        summary = run_llm(summary_prompt)
        if is_valid_summary(summary, topic):
            return summary
        logger.error(f"Invalid summary on attempt {attempt}")

        if attempt < 3:
            appendix = "\n\n(This is attempt {attempt}. The previous summary was invalid. Try harder!)"
            summary_prompt += appendix.format(attempt=attempt + 1)

    return ""
