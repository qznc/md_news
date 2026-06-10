"""Summary validation utilities for md-news."""

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from lib.llm import run_llm
from lib.logging import logger
from lib.web import fetch_urls


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
) -> tuple[Dict[str, Any], str]:
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
        try:
            select_response, select_model = run_llm(select_prompt)
        except Exception as e:
            logger.warning(f"LLM Select failed: {e}")
            continue
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

        url_contents_dict = fetch_urls(urls)

        # If we have at least 3 successful URLs, return the result
        if len(url_contents_dict) >= 3:
            return {"topic": topic, "urls": url_contents_dict}, select_model
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
    if not summary:
        logger.debug("summary proposal is None")
        return False
    if not summary.strip():
        logger.debug("summary proposal is empty")
        return False
    if len(summary) < 200:
        logger.debug("summary proposal is too short")
        return False
    if not summary.lstrip().startswith("# "):
        logger.debug("summary proposal does not start with Markdown h1")
        return False
    if "[" not in summary or "](" not in summary:
        logger.debug("summary proposal does not contain a Markdown link")
        return False
    if "---" not in summary:
        logger.debug("summary proposal does not contain ---")
        return False
    if "Grumpy's commentary:" not in summary:
        logger.debug("summary proposal misses Grumpy")
        return False
    if "Bubbles's commentary:" not in summary:
        logger.debug("summary proposal misses Bubbles")
        return False
    if summary.count("\n\n") < 2:
        logger.debug("summary proposal lacks parapgraphs")
        return False
    return True


def generate_summary(
    summary_prompt_template: str,
    tmp_dir: str,
    topic: str,
    urls_text: str,
    thinking: bool = True,
) -> tuple[str, str]:
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
        appendix = (
            f"\n\n(This is attempt {attempt}. The previous summary was invalid. Try harder!)"
            if attempt >= 2
            else ""
        )
        p = summary_prompt + appendix
        with open(f"{tmp_dir}/_3_summary_prompt.txt", "w") as f:
            f.write(p)
        summary, model = run_llm(p, thinking=thinking)
        with open(f"{tmp_dir}/_4_summary.txt", "w") as f:
            f.write(summary)
        if is_valid_summary(summary, topic):
            return summary, model
        logger.error(f"Invalid summary on attempt {attempt}")
    raise Exception("No more attempts")


def gen_footer(source_info: str, select_model: str, summary_model: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if select_model == summary_model:
        models_str = f"with {select_model}"
    else:
        models_str = f"with {select_model} and {summary_model}"

    return (
        f"\n\n---\n\n"
        f"Generated at {timestamp} from {source_info} {models_str}\n\n"
        f"Licensed under [Creative Commons Zero](https://creativecommons.org/publicdomain/zero/1.0/) (CC0 1.0 Universal)"
    )
