#!/usr/bin/env python3
"""
Generate a Markdown article from HN frontpage data using LLM.
"""

from datetime import datetime
from typing import Any, Dict, List

from hn_frontpage import get_frontpage_output
from lib.summary import generate_summary, select_topic_and_urls
from lib.web import fetch_url_contents
from lib.logging import logger

HN_FRONTPAGE_URL = "https://news.ycombinator.com"

SELECT_PROMPT = """
Analyze the HN frontpage stories below.
Consider upvotes, comments, and order.
Then pick ONE SPECIFIC TOPIC that would make for an interesting article.

For your chosen topic, select 3-4 most relevant URLs of relevant sources.
At least one URL should be a discussion thread on HN.

Respond ONLY with a JSON object in this exact format:
{{
    "topic": "the topic you chose",
    "urls": ["url1", "url2", ...]
}}

Do NOT include any other text, explanations, or markdown. Just the JSON.

```HN Frontpage Stories:
{posts_text}
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
# <Attention-grabbing title (do not reuse any HN title!)>

<one paragraph: summary explaining the relevance of [the topic](central url) and why it's interesting, without repeating the title.>

<multiple paragraphs expanding the summary providing context and explanation.
[Reference sources from above](some url) with Markdown links.
Use simple language, avoid jargon, and explain terms.>

---

Grumpy's commentary: <short sarcastic biting commentary with a touch of cynicism>

Bubbles's commentary: <overly cheerful optimistic commentary with emojis>

Koan's commentary: <crack some incomprehensible zen-like wisdom sentence>
```

Respond with only the article and nothing else.
"""


def format_stories_for_prompt(stories: List[Dict[str, Any]]) -> str:
    """Format stories for the LLM prompt."""
    lines = []
    for i, story in enumerate(stories, 1):
        title = story.get("title", "No title")
        url = story.get("url", "No URL")
        score = story.get("score", 0)
        comments = story.get("descendants", 0)
        lines.append(f"{i}. {title}")
        lines.append(f"   URL: {url}")
        lines.append(f"   Score: {score} | Comments: {comments}")
    return "\n".join(lines)


def generate_hn_summary() -> str:
    """
    Generate a Markdown article from HN frontpage data using the LLM.
    """
    import os

    tmp_dir = "_tmp/hn"
    os.makedirs(tmp_dir, exist_ok=True)

    stories_text = get_frontpage_output()
    topic, urls = select_topic_and_urls(SELECT_PROMPT, stories_text, tmp_dir)

    if not topic or not urls:
        return "Error: Invalid response from LLM in step 1 after 3 attempts"

    # Step 2: Fetch URL contents
    urls_text = fetch_url_contents(urls)

    # Step 3: Generate summary with fetched content
    summary = generate_summary(
        SUMMARY_PROMPT_TEMPLATE, tmp_dir, topic, urls_text, thinking=False
    )

    return summary


if __name__ == "__main__":
    summary = generate_hn_summary()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = f"\n---\n\nGenerated at {timestamp} from [Hacker News]({HN_FRONTPAGE_URL})\n\nLicensed under [Creative Commons Zero](https://creativecommons.org/publicdomain/zero/1.0/) (CC0 1.0 Universal)"
    logger.info(f"Generated summary:\n{summary + footer}")
    print(summary + footer)
