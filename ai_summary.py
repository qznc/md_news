#!/usr/bin/env python3
"""
Generate a Markdown article from AI subreddits data using LLM.
"""

import json
import re
import sys
from datetime import datetime
from typing import Optional

from lib.llm import run_llm
from lib.summary import is_valid_summary
from lib.web import fetch_url_content, fetch_url_contents
from reddit_ai import get_ai_subreddits_output

REDIT_FRONTPAGE_URL = "https://old.reddit.com"

SELECT_PROMPT = """
Analyze the Reddit AI communities posts below.
Focus on topics which come up in multiple subreddits.
Then pick ONE SPECIFIC TOPIC that would make for an interesting article.

For your chosen topic, select 3-4 most relevant URLs of relevant sources.
At least two URLs should be not from Reddit.

Respond ONLY with a JSON object in this exact format:
{{
    "topic": "the topic you chose",
    "urls": ["url1", "url2", ...]
}}

Do NOT include any other text, explanations, or markdown. Just the JSON.

```Reddit AI Posts:
{ai_posts}
```
"""

SUMMARY_PROMPT_TEMPLATE = """
Write a Markdown article about the topic: {topic}

Use the fetched content from these URLs as your source material:

{url_contents}

## Requirements:

- Use proper Markdown formatting.
- Use line breaks after each sentence.
- Keep the tone terse, professional, and informative.

```Article template:
# <Attention-grabbing title (do not reuse any Reddit title!)>

<one paragraph: summary explaining the relevance of [the topic](central url) and why it's interesting, without repeating the title.>

<multiple paragraphs expanding the summary providing context and explanation.
[Reference sources from above](some url) with Markdown links.
Use simple language, avoid jargon, and explain terms.>

---

Grumpy's commentary: <short sarcastic biting commentary with a touch of cynicism>

Bubbles's commentary: <overly cheerful optimistic commentary with emojis>

Koan's commentary: <crack some incomprehensible zen-like wisdom sentence>
```

Respond with ONLY the article and nothing else.
"""


def _select_topic_and_urls(tmp_dir: str, posts_text: str) -> tuple[Optional[str], list[str]]:
    """
    Use LLM to select a topic and URLs from AI subreddit posts.
    Retries up to 3 times if the response is invalid.
    Returns (topic, urls) tuple.
    """
    select_prompt = SELECT_PROMPT.format(ai_posts=posts_text)

    for attempt in range(1, 4):
        print(f"Step 1 attempt {attempt}/3", file=sys.stderr)
        with open(f"{tmp_dir}/_1_select_prompt.txt", "w") as f:
            f.write(select_prompt)
        select_response = run_llm(select_prompt)
        with open(f"{tmp_dir}/_2_select_response.txt", "w") as f:
            f.write(select_response)

        json_match = re.search(r"\{[^\}]*\}", select_response, re.DOTALL)
        if not json_match:
            print(
                f"Error: Could not find JSON in LLM response on attempt {attempt}. Response was:",
                select_response,
                file=sys.stderr,
            )
            continue

        try:
            selection = json.loads(json_match.group(0))
            topic = selection.get("topic", "Untitled Topic")
            urls = selection.get("urls", [])
        except json.JSONDecodeError as e:
            print(
                f"Error parsing JSON on attempt {attempt}: {e}. Response was: {select_response}",
                file=sys.stderr,
            )
            continue

        if urls:
            return topic, urls
        else:
            print(
                f"Error: No URLs selected by LLM on attempt {attempt}", file=sys.stderr
            )

    return None, []



def _generate_summary(tmp_dir: str, topic: str, urls_text: str) -> str:
    """
    Generate the final summary article using the LLM.
    Retries up to 3 times if the summary is invalid.
    """
    summary_prompt = SUMMARY_PROMPT_TEMPLATE.format(topic=topic, url_contents=urls_text)
    with open(f"{tmp_dir}/_3_summary_prompt.txt", "w") as f:
        f.write(summary_prompt)

    for attempt in range(1, 4):
        print(f"Step 2 attempt {attempt}/3", file=sys.stderr)
        summary = run_llm(summary_prompt)
        if is_valid_summary(summary, topic):
            return summary
        print(f"Error: Invalid summary on attempt {attempt}", file=sys.stderr)

    return ""


def generate_ai_summary() -> str:
    """
    Generate a Markdown article from AI subreddits data using the LLM.
    
    Steps:
    1. Get AI subreddit posts and use LLM to select a topic and URLs
    2. Fetch content from the selected URLs
    3. Generate the final summary article using the fetched content
    """
    import os

    tmp_dir = "_tmp/ai"
    os.makedirs(tmp_dir, exist_ok=True)

    posts_text = get_ai_subreddits_output()
    topic, urls = _select_topic_and_urls(tmp_dir, posts_text)

    if not topic or not urls:
        return "Error: Invalid response from LLM in step 1 after 3 attempts"

    urls_text = fetch_url_contents(urls)
    summary = _generate_summary(tmp_dir, topic, urls_text)

    return summary


if __name__ == "__main__":
    summary = generate_ai_summary()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = f"\n---\n\nGenerated at {timestamp} from AI subreddits on [Reddit]({REDIT_FRONTPAGE_URL})\n\nLicensed under [Creative Commons Zero](https://creativecommons.org/publicdomain/zero/1.0/) (CC0 1.0 Universal)"
    print(summary + footer)
