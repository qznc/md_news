#!/usr/bin/env python3
"""LLM utilities for md-news."""

import subprocess
import sys

from lib.logging import logger

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
        logger.error(f"Error running llm: {e}")
        return f"Error generating summary: {e}"
    except FileNotFoundError:
        logger.error(
            "Error: 'vibe' executable not found. Make sure it's installed and in PATH."
        )
        return "Error: vibe executable not found"
