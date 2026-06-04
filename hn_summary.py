#!/usr/bin/env python3
"""
Generate a Markdown article from HN frontpage data using LLM.
Two-step process:
1. LLM picks a topic and which URLs are relevant.
2. Fetch URL contents (lynx -dump) and do the summary.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List

from hn_frontpage import get_frontpage_output

# Maximum lines to fetch from each URL
MAX_LINES_PER_URL = 200

# HN frontpage URL for footer
HN_FRONTPAGE_URL = "https://news.ycombinator.com"

SELECT_PROMPT = """
Analyze the HN frontpage stories below and pick ONE topic that is most generally relevant and would make for an interesting article.

For your chosen topic, select 2-4 most relevant URLs from the stories that relate to that topic.

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
- Use simple language, avoid jargon, and explain terms.
- Use hyperlinks to reference sources.

```Article template:
# <Attention-grabbing title (do not reuse any HN title!)>

<one paragraph: short summary integrating the article URL>

<multiple paragraphs expanding the summary providing context, explanation, and assessing the general relevance of the topic>

Grumpy's commentary: <sarcastic biting commentary with a touch of cynicism>

Bubbles's commentary: <an overly cheerful optimistic commentary with emojis>
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


def fetch_url_content(url: str) -> str:
    """Fetch URL content using lynx -dump, limited to MAX_LINES_PER_URL lines."""
    try:
        result = subprocess.run(
            ["lynx", "-dump", "-nolist", url],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"Error fetching {url}: {result.stderr}"
        lines = result.stdout.splitlines()
        return "\n".join(lines[:MAX_LINES_PER_URL])
    except subprocess.TimeoutExpired:
        return f"Timeout fetching {url}"
    except FileNotFoundError:
        return f"Error: lynx not found. Cannot fetch {url}"


def run_llm(prompt: str) -> str:
    """Run the LLM with the given prompt."""
    try:
        result = subprocess.run(
            ["vibe", "-p"], input=prompt, text=True, capture_output=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running llm: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        return f"Error generating summary: {e}"
    except FileNotFoundError:
        print(
            "Error: 'vibe' executable not found. Make sure it's installed and in PATH.",
            file=sys.stderr,
        )
        return "Error: vibe executable not found"


def generate_hn_summary() -> str:
    """
    Generate a Markdown article from HN frontpage data using the LLM.
    Two-step process:
    1. LLM picks a topic and which URLs are relevant.
    2. Fetch URL contents (lynx -dump) and do the summary.
    """

    # Step 1: Get stories and have LLM pick topic and URLs
    stories_text = get_frontpage_output(limit=50)
    select_prompt = SELECT_PROMPT.format(hn_stories=stories_text)
    with open("_1_select_prompt.txt", "w") as f:
        f.write(select_prompt)
    select_response = run_llm(select_prompt)
    with open("_2_select_response.txt", "w") as f:
        f.write(select_response)

    json_match = re.search(r"\{[^}]*\}", select_response, re.DOTALL)
    if not json_match:
        print(
            "Error: Could not find JSON in LLM response. Response was:",
            select_response,
            file=sys.stderr,
        )
        return "Error: Invalid response from LLM in step 1"

    try:
        selection = json.loads(json_match.group(0))
        topic = selection.get("topic", "Untitled Topic")
        urls = selection.get("urls", [])
    except json.JSONDecodeError as e:
        print(
            f"Error parsing JSON: {e}. Response was: {select_response}", file=sys.stderr
        )
        return "Error: Invalid JSON from LLM in step 1"

    if not urls:
        return "Error: No URLs selected by LLM"

    # Step 2: Fetch URL contents
    url_contents = []
    for url in urls:
        print(f"Fetching: {url}", file=sys.stderr)
        content = fetch_url_content(url)
        url_contents.append(f"URL: {url}\nContent:\n{content}\n")

    urls_text = "\n\n".join(url_contents)

    # Step 3: Generate summary with fetched content
    summary_prompt = SUMMARY_PROMPT_TEMPLATE.format(topic=topic, url_contents=urls_text)
    with open("_3_summary_prompt.txt", "w") as f:
        f.write(summary_prompt)
    summary = run_llm(summary_prompt)

    return summary


if __name__ == "__main__":
    summary = generate_hn_summary()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = f"\n---\n\nGenerated at {timestamp} from [Hacker News]({HN_FRONTPAGE_URL})\n\nLicensed under [Creative Commons Zero](https://creativecommons.org/publicdomain/zero/1.0/) (CC0 1.0 Universal)"
    print(summary + footer)
