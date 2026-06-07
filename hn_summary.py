#!/usr/bin/env python3
"""
Generate a Markdown article from HN frontpage data using LLM.
"""

import json
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from hn_frontpage import get_frontpage_output
from lib.llm import run_llm
from lib.summary import is_valid_summary
from lib.web import fetch_url_content, fetch_url_contents

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
{hn_stories}
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
    select_prompt = SELECT_PROMPT.format(hn_stories=stories_text)

    selection = None
    for attempt in range(1, 4):
        print(f"Step 1 attempt {attempt}/3", file=sys.stderr)
        with open(f"{tmp_dir}/_1_select_prompt.txt", "w") as f:
            f.write(select_prompt)
        select_response = run_llm(select_prompt)
        with open(f"{tmp_dir}/_2_select_response.txt", "w") as f:
            f.write(select_response)

        json_match = re.search(r"\{[^}]*\}", select_response, re.DOTALL)
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
            break
        else:
            print(
                f"Error: No URLs selected by LLM on attempt {attempt}", file=sys.stderr
            )

    if selection is None or not urls:
        return "Error: Invalid response from LLM in step 1 after 3 attempts"

    # Step 2: Fetch URL contents
    urls_text = fetch_url_contents(urls)

    # Step 3: Generate summary with fetched content
    summary_prompt = SUMMARY_PROMPT_TEMPLATE.format(topic=topic, url_contents=urls_text)
    with open(f"{tmp_dir}/_3_summary_prompt.txt", "w") as f:
        f.write(summary_prompt)
    summary = ""
    for attempt in range(1, 4):
        print(f"Step 2 attempt {attempt}/3", file=sys.stderr)
        summary = run_llm(summary_prompt)
        if is_valid_summary(summary, topic):
            break
        print(f"Error: Invalid summary on attempt {attempt}", file=sys.stderr)

    return summary


if __name__ == "__main__":
    summary = generate_hn_summary()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = f"\n---\n\nGenerated at {timestamp} from [Hacker News]({HN_FRONTPAGE_URL})\n\nLicensed under [Creative Commons Zero](https://creativecommons.org/publicdomain/zero/1.0/) (CC0 1.0 Universal)"
    print(summary + footer)
