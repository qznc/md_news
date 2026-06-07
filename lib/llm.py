#!/usr/bin/env python3
"""LLM utilities for md-news."""

import subprocess
import sys

LLM_COMMAND = ["vibe", "-p"]


def run_llm(prompt: str) -> str:
    """Run the LLM with the given prompt.
    
    Returns:
        The LLM output as a string, or an error message if it fails.
    """
    try:
        result = subprocess.run(
            LLM_COMMAND + [prompt],
            text=True,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running llm: {e}", file=sys.stderr)
        return f"Error generating summary: {e}"
    except FileNotFoundError:
        print(
            "Error: 'vibe' executable not found. Make sure it's installed and in PATH.",
            file=sys.stderr,
        )
        return "Error: vibe executable not found"
