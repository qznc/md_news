#!/usr/bin/env python3
"""
Generate a Markdown article from AI subreddits data using LLM.
"""

from lib.logging import logger
from lib.summary import (
    format_url_contents,
    gen_footer,
    generate_summary,
    select_topic_and_urls,
)
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
- Link texts must be unique and meaningful on its own for accessability.
- Use line breaks after each sentence.
- Keep the tone terse, professional, and informative.

```Article template:
# <Attention-grabbing title (do not reuse any Reddit title!)>

<one paragraph: summary explaining the relevance of [the topic](central url) and why it's interesting, without repeating the title.>

<multiple paragraphs expanding the summary providing context and explanation.
Reference all [sources from above](some url) with Markdown links.
Use simple language, avoid jargon, and explain terms.>

---

Grumpy's commentary: <short sarcastic biting commentary with a touch of cynicism>

Bubbles's commentary: <overly cheerful optimistic commentary with emojis>

Koan's commentary: <crack some strange zen-like wisdom sentence>
```

Respond with ONLY the article and nothing else.
"""


def generate_ai_summary() -> tuple[str, str, str]:
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
    selection, select_model = select_topic_and_urls(SELECT_PROMPT, posts_text, tmp_dir)

    topic_obj = selection.get("topic")
    topic = topic_obj if isinstance(topic_obj, str) else "Untitled Topic"
    urls_dict = selection.get("urls")
    if not isinstance(urls_dict, dict):
        urls_dict = {}

    urls_text = format_url_contents(urls_dict)
    summary, summary_model = generate_summary(
        SUMMARY_PROMPT_TEMPLATE, tmp_dir, topic, urls_text
    )

    return summary, select_model, summary_model


if __name__ == "__main__":
    summary, select_model, summary_model = generate_ai_summary()
    footer = gen_footer(
        f"AI subreddits on [Reddit]({REDIT_FRONTPAGE_URL})",
        select_model,
        summary_model,
    )
    print(summary + footer)
