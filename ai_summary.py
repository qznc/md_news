#!/usr/bin/env python3
"""
Generate a Markdown article from AI subreddits data using LLM.
"""

from datetime import datetime

from lib.logging import logger
from lib.summary import format_url_contents, generate_summary, select_topic_and_urls
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
    selection = select_topic_and_urls(SELECT_PROMPT, posts_text, tmp_dir)

    topic = selection.get("topic")
    urls_dict = selection.get("urls", {})

    urls_text = format_url_contents(urls_dict)
    summary = generate_summary(SUMMARY_PROMPT_TEMPLATE, tmp_dir, topic, urls_text)

    return summary


if __name__ == "__main__":
    summary = generate_ai_summary()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = f"\n---\n\nGenerated at {timestamp} from AI subreddits on [Reddit]({REDIT_FRONTPAGE_URL})\n\nLicensed under [Creative Commons Zero](https://creativecommons.org/publicdomain/zero/1.0/) (CC0 1.0 Universal)"
    logger.info(f"Generated summary:\n{summary + footer}")
    print(summary + footer)
