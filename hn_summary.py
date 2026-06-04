#!/usr/bin/env python3
"""
Generate a Markdown article from HN frontpage data using LLM.
"""

import subprocess
import sys

from hn_frontpage import get_frontpage_output

MARKDOWN_TEMPLATE = """
Pick *one* topic from the HN frontpage data below and write a Markdown summary about that topic.

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

```HN Frontpage Data:
{hn_data}
```

Pick the most relevant topic from the HN frontpage data below and write a Markdown summary about that topic.
Respond with only the article and nothing else.
"""


def generate_hn_summary() -> str:
    """
    Generate a Markdown article from HN frontpage data using the LLM.
    """
    hn_data = get_frontpage_output()
    prompt = MARKDOWN_TEMPLATE.format(hn_data=hn_data)
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
            "Error: 'llm' executable not found. Make sure it's installed and in PATH.",
            file=sys.stderr,
        )
        return "Error: llm executable not found"


if __name__ == "__main__":
    summary = generate_hn_summary()
    print(summary)
