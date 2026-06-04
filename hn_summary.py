#!/usr/bin/env python3
"""
Generate a Markdown article from HN frontpage data using LLM.
"""

import subprocess
import sys

from hn_frontpage import get_frontpage_output

# Markdown article template with instructions for the LLM
MARKDOWN_TEMPLATE = """
Pick *one* topic from the HN frontpage data below and write a Markdown summary about that topic.

## Requirements:
#
- Use proper Markdown formatting.
- Use line breaks after each sentence.
- Keep the tone terse, professional, and informative.
- Use hyperlinks to reference sources.

```Article template:
# <Attention-grabbing title (do not reuse any HN title!)>

<one paragraph: short summary>

<multiple paragraphs expanding the summary with insights, context, and analysis>

Grumpy's commentary: <a sarcastic commentary towards Hacker News>
```

```HN Frontpage Data:
{hn_data}
```

Pick *one* topic from the HN frontpage data below and write a Markdown summary about that topic.
Respond with only the article and nothing else.
"""


def generate_hn_summary() -> str:
    """
    Generate a Markdown article from HN frontpage data using the LLM.

    Returns:
        str: The generated Markdown article
    """
    # Get the HN frontpage data
    hn_data = get_frontpage_output()

    # Create the full prompt by inserting HN data into template
    prompt = MARKDOWN_TEMPLATE.format(hn_data=hn_data)

    # Run the prompt through the llm executable
    try:
        result = subprocess.run(
            ["llm"], input=prompt, text=True, capture_output=True, check=True
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


def main():
    """Main function to generate and print the HN summary article."""
    summary = generate_hn_summary()
    print(summary)


if __name__ == "__main__":
    main()
