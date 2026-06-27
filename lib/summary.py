"""Summary validation utilities for md-news."""

import json
import re
from datetime import datetime
from typing import Any, Dict

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


def select_topic_and_urls(prompt: str, tmp_dir: str) -> tuple[Dict[str, Any], str]:
    """Use LLM to select a topic and URLs from posts.

    Args:
        prompt: Fully formatted prompt string to send to the LLM
        tmp_dir: Temporary directory for debugging files

    Retries up to 3 times if the response is invalid.
    Failed URLs are filtered out as long as at least 3 successful URLs remain.
    Returns a dict with 'topic' and 'urls' keys, where 'urls' is a dict mapping
    URLs to their fetched content.

    Raises:
        RuntimeError: If all attempts fail or if fewer than 3 URLs can be fetched.
    """

    for attempt in range(1, 4):
        logger.info(f"Step 1 selection attempt {attempt}/3")
        with open(f"{tmp_dir}/_1_select_prompt.txt", "w") as f:
            f.write(prompt)
        try:
            select_response, select_model = run_llm(prompt)
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

        # minimum successful URLs necessary
        if len(url_contents_dict) >= 2:
            logger.info(f"Selected topic: {topic}")
            return {"topic": topic, "urls": url_contents_dict}, select_model
        else:
            logger.error(
                f"Too few URLs succeeded (got {len(url_contents_dict)}) on attempt {attempt}"
            )
            continue

    raise RuntimeError("Failed to select topic")


def _summary_error(summary: str) -> str | None:
    """Return reason why summary is invalid"""
    if not summary:
        return "no summary"
    if not summary.strip():
        return "empty summary"
    if len(summary) < 200:
        return "summary too short"
    if not summary.lstrip().startswith("# "):
        return "summary does not start with Markdown h1 '#'"
    if "[" not in summary or "](" not in summary:
        return "summary has no [Markdown](url) link"
    if summary.count("\n\n") < 2:
        return "summary lacks parapgraphs"
    return None


def generate_summary(
    summary_prompt_template: str,
    tmp_dir: str,
    topic: str,
    urls_text: str,
    thinking: bool = True,
    retries: int = 2,
) -> tuple[str, str]:
    """Generate the final summary article using the LLM.

    Args:
        summary_prompt_template: The template string for the summary prompt
        tmp_dir: Temporary directory for debugging files
        topic: The topic for the summary
        urls_text: Formatted URL contents
        thinking: Whether to enable reasoning effort (default: True for ai_summary)
        retries: Number of retries if the summary is invalid.

    Retries up to the given number of times.
    """
    summary_prompt = summary_prompt_template.format(topic=topic, url_contents=urls_text)
    err = None

    for attempt in range(1, retries + 2):
        logger.info(f"Step 2 summary attempt {attempt}")
        appendix = ""
        if attempt >= 2:
            appendix = f"\n\n(This is attempt {attempt}. The previous summary was invalid: {err} Try harder!)"
        p = summary_prompt + appendix
        with open(f"{tmp_dir}/_3_summary_prompt.txt", "w") as f:
            f.write(p)
        summary, model = run_llm(p, thinking=thinking)
        with open(f"{tmp_dir}/_4_summary.txt", "w") as f:
            f.write(summary)
        err = _summary_error(summary)
        if not err:
            return summary, model
        logger.error(f"Invalid summary on attempt {attempt}: {err}")
    raise Exception("No more attempts")


def _commentaries_error(commentaries: str) -> str | None:
    """Return reason why commentaries are invalid"""
    for name in ("Grumpy", "Bubbles", "Koan"):
        if name not in commentaries:
            return "commentaries miss " + name
    count_par_seps = commentaries.count("\n\n")
    if count_par_seps < 2:
        return "commentaries must be separated by double newlines"
    return None


def generate_commentaries(
    commentary_prompt_template: str,
    tmp_dir: str,
    article: str,
    thinking: bool = False,
    retries: int = 2,
) -> tuple[str, str]:
    """Generate commentaries for the given article using the LLM.

    Args:
        commentary_prompt_template: The template string for the commentary prompt
        tmp_dir: Temporary directory for debugging files
        article: The generated article
        thinking: Whether to enable reasoning effort
        retries: Number of retries if the output is invalid.
    """
    prompt = commentary_prompt_template.format(article=article)
    err = None

    for attempt in range(1, retries + 2):
        logger.info(f"Step 3 commentary attempt {attempt}")
        appendix = ""
        if attempt >= 2:
            appendix = f"\n\n(This is attempt {attempt}. The previous output was invalid: {err} Try harder!)"
        p = prompt + appendix
        with open(f"{tmp_dir}/_5_commentary_prompt.txt", "w") as f:
            f.write(p)
        commentaries, model = run_llm(p, thinking=thinking)
        with open(f"{tmp_dir}/_6_commentary.txt", "w") as f:
            f.write(commentaries)
        err = _commentaries_error(commentaries)
        if not err:
            return commentaries, model
        logger.error(f"Invalid commentaries on attempt {attempt}: {err}")
    raise Exception("No more attempts")


def gen_footer(source_info: str, *models: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    unique_models = []
    for m in models:
        if m and m not in unique_models:
            unique_models.append(m)

    if len(unique_models) == 1:
        models_str = f"with {unique_models[0]}"
    elif len(unique_models) > 1:
        models_str = f"with {', '.join(unique_models[:-1])} and {unique_models[-1]}"
    else:
        models_str = ""

    return (
        f"\n\n---\n\n"
        f"Generated at {timestamp} from {source_info} {models_str}\n\n"
        f"Licensed under [Creative Commons Zero](https://creativecommons.org/publicdomain/zero/1.0/) (CC0 1.0 Universal)"
    )
