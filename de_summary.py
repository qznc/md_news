#!/usr/bin/env python3
"""
Generate a Markdown article from r/de subreddit data using LLM.
The output is in German.
"""

from lib.logging import logger
from lib.summary import (
    format_url_contents,
    gen_footer,
    generate_summary,
    select_topic_and_urls,
)
from reddit_de import get_de_subreddits_output

REDIT_FRONTPAGE_URL = "https://old.reddit.com"

SELECT_PROMPT = """
Analyse the following submissions to the r/de subreddit for relevance and usefulness.
Specify a SINGLE SPECIFIC topic for an interesting article in German.

Also, select 3-5 relevant URLs from the sources.
At least one URL from reddit and one not.

Answer only with a raw JSON object in this format:
{{
    "topic": "das gewählte Thema",
    "urls": ["url1", "url2", ...]
}}

Add no further text, explanation, or markdown. Only the JSON.

```posts from r/de:
{posts_text}
```
"""

SUMMARY_PROMPT_TEMPLATE = """
Write a German article using Markdown syntax about: {topic}

Use the content from these URLs as sources:

{url_contents}

## Requirements:

- Use correct Markdown syntax
- Newlines after every sentence.
- Keep the tone terse, professional, and informative.

```article-template
# <Aufmerksamkeitserregende Überschrift (verwende keinen Reddit-Titel nochmal!)>

<one paragraph: Zusammenfassung, die die Relevanz von [dem Thema](zentrale URL) erklärt und warum es interessant ist, ohne die Überschrift zu wiederholen.>

<multiple paragraphs expanding the summary providing context and explanation.
Reference all [sources from above](some url) with Markdown links.
Use simple language, avoid jargon, and explain terms.>

---

Grumpys Kommentar: <kurzer sarkastischer, beißender Kommentar mit einer Prise Zynismus>

Bubbles' Kommentar: <übertrieben fröhlicher, optimistischer Kommentar mit Emojis>

Koans Kommentar: <ein seltsamer, zen-ähnlicher Weisheitsspruch>
```

Respond only with the article and nothing else.
"""


def generate_de_summary() -> tuple[str, str, str]:
    """
    Generate a Markdown article from German subreddits data using the LLM.
    """
    import os

    tmp_dir = "_tmp/de"
    os.makedirs(tmp_dir, exist_ok=True)

    posts_text = get_de_subreddits_output()
    selection, select_model = select_topic_and_urls(SELECT_PROMPT, posts_text, tmp_dir)

    topic_obj = selection.get("topic")
    topic = topic_obj if isinstance(topic_obj, str) else "Unbenannter Titel"
    urls_dict = selection.get("urls")
    if not isinstance(urls_dict, dict):
        urls_dict = {}

    urls_text = format_url_contents(urls_dict)
    summary, summary_model = generate_summary(
        SUMMARY_PROMPT_TEMPLATE, tmp_dir, topic, urls_text
    )

    return summary, select_model, summary_model


if __name__ == "__main__":
    summary, select_model, summary_model = generate_de_summary()
    footer = gen_footer(
        f"Deutschsprachige Communities auf [Reddit]({REDIT_FRONTPAGE_URL})",
        select_model,
        summary_model,
    )
    print(summary + footer)
