#!/usr/bin/env python3
"""
Generate a Markdown article from r/de subreddit data using LLM.
The output is in German.
"""

import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

from lib.logging import logger
from lib.summary import (
    format_url_contents,
    gen_footer,
    gen_models_str,
    generate_commentaries,
    generate_summary,
    select_topic_and_urls,
)
from reddit_de import get_de_subreddits_output

REDIT_FRONTPAGE_URL = "https://old.reddit.com"
TAGESSCHAU_FEED_URL = "https://www.tagesschau.de/index~atom.xml"

SELECT_PROMPT = """
Analyse the following submissions to the r/de subreddit AND the latest news from Tagesschau for relevance and usefulness.
Specify a SINGLE SPECIFIC topic for an engaging article in German.

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

```news from tagesschau:
{tagesschau_text}
```
"""

SUMMARY_PROMPT_TEMPLATE = """
Write an engaging German article using Markdown syntax about: {topic}
Focus on the pros and cons of the Reddit discussion and if there is a conclusion.

Use the content from these URLs as sources:

{url_contents}

## Requirements:

- Use correct Markdown syntax
- Link texts must be unique and meaningful on its own for accessability.
- Newlines after every sentence.
- Keep the tone terse, professional, and informative.

```article-template
# <Aufmerksamkeitserregende Überschrift (verwende keinen Reddit-Titel nochmal!)>

<one paragraph: Zusammenfassung, die die Relevanz von [dem Thema](zentrale URL) erklärt und warum es interessant ist, ohne die Überschrift zu wiederholen.>

<multiple paragraphs expanding the summary providing context and explanation.
Reference all [sources from above](some url) with Markdown links.
Use simple language, avoid jargon, and explain terms.>
```

Respond only with the article and nothing else.
"""

COMMENTARY_PROMPT_TEMPLATE = """
Lies den folgenden Artikel und schreibe drei kurze Kommentare aus der Perspektive von drei verschiedenen Charakteren.

```Artikel
{article}
```

Antworte NUR mit den drei Kommentaren in genau diesem Format:

Grumpys Kommentar: <kurzer sarkastischer, beißender Kommentar mit einer Prise Zynismus>

Bubbles' Kommentar: <übertrieben fröhlicher, optimistischer Kommentar mit Emojis>

Koans Kommentar: <ein sehr kurzer, seltsamer, zen-ähnlicher Weisheitsspruch>
"""


def fetch_tagesschau_feed() -> str:
    """Fetch and format the latest news from Tagesschau Atom feed."""
    namespaces = {
        "atom": "http://purl.org/atom/ns#",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    try:
        req = Request(TAGESSCHAU_FEED_URL, headers={"User-Agent": "md-news/1.0"})
        with urlopen(req, timeout=30) as response:
            xml_content = response.read().decode("utf-8")

        root = ET.fromstring(xml_content)
        entries = []

        # Find all entry elements using the atom namespace
        for entry in root.findall(".//atom:entry", namespaces):
            title = entry.find("atom:title", namespaces)
            title_text = title.text if title is not None else "No title"

            # Get the link URL
            url = ""
            for link in entry.findall("atom:link", namespaces):
                if "href" in link.attrib:
                    url = link.attrib["href"]
                    break

            # Get published date - tagesschau uses dc:date

            # Get summary - tagesschau uses summary with type="text/html"
            summary = entry.find("atom:summary", namespaces)
            content = entry.find("atom:content", namespaces)
            content_text = ""
            if summary is not None and summary.text:
                content_text = summary.text
            elif content is not None and content.text:
                content_text = content.text

            if title_text and url:
                entry_lines = [f"- {title_text}"]
                if url:
                    entry_lines.append(f"  URL: {url}")
                if content_text:
                    entry_lines.append(f"  Summary: {content_text}")
                entries.append("\n".join(entry_lines))

        if entries:
            header = "Tagesschau Latest News"
            return f"{header}\n\n" + "\n\n".join(entries) + "\n"
        else:
            return "No Tagesschau news items found"

    except Exception as e:
        logger.warning(f"Failed to fetch Tagesschau feed: {e}")
        return "Tagesschau feed unavailable"


def generate_de_summary() -> tuple[str, str, str, str]:
    """
    Generate a Markdown article from German subreddits data using the LLM.
    """
    import os

    tmp_dir = "_tmp/de"
    os.makedirs(tmp_dir, exist_ok=True)

    posts_text = get_de_subreddits_output()
    tagesschau_text = fetch_tagesschau_feed()
    prompt = SELECT_PROMPT.format(
        posts_text=posts_text, tagesschau_text=tagesschau_text
    )
    selection, select_model = select_topic_and_urls(prompt, tmp_dir)

    topic_obj = selection.get("topic")
    topic = topic_obj if isinstance(topic_obj, str) else "Unbenannter Titel"
    urls_dict = selection.get("urls")
    if not isinstance(urls_dict, dict):
        urls_dict = {}

    urls_text = format_url_contents(urls_dict)
    summary, summary_model = generate_summary(
        SUMMARY_PROMPT_TEMPLATE, tmp_dir, topic, urls_text, retries=6
    )

    commentaries, commentary_model = generate_commentaries(
        COMMENTARY_PROMPT_TEMPLATE, tmp_dir, summary, thinking=True, retries=2
    )

    return (
        summary + "\n\n---\n\n" + commentaries,
        select_model,
        summary_model,
        commentary_model,
    )


if __name__ == "__main__":
    summary, select_model, summary_model, commentary_model = generate_de_summary()
    header = gen_models_str(select_model, summary_model, commentary_model)
    footer = gen_footer(
        f"Deutschsprachige Communities auf [Reddit]({REDIT_FRONTPAGE_URL})",
        select_model,
        summary_model,
        commentary_model,
    )
    print(header + summary + footer)
