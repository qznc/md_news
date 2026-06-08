#!/usr/bin/env python3
"""LLM utilities for md-news using Mistral REST API."""

import json
import os
import urllib.error
import urllib.request
from typing import Any

from lib.logging import logger

# Configuration
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = "mistral-medium-latest"
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.3


def _get_api_key() -> str:
    """Get the Mistral API key from .env file.

    Returns:
        The API key as a string.

    Raises:
        ValueError: If API key is not found.
    """
    # Try to read from .env file first
    env_path = ".env"
    api_key = None

    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == "MISTRAL_API_KEY":
                            api_key = value.strip()
                            # Remove surrounding quotes if present
                            if (api_key.startswith('"') and api_key.endswith('"')) or (
                                api_key.startswith("'") and api_key.endswith("'")
                            ):
                                api_key = api_key[1:-1]
                            break
    except FileNotFoundError:
        pass

    # Fall back to environment variable
    if not api_key:
        api_key = os.environ.get("MISTRAL_API_KEY")

    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY not found. Set it in .env file or environment variable. "
            "Get one at https://console.mistral.ai"
        )

    return api_key


def _make_api_request(prompt: str, model: str, max_tokens: int, temperature: float) -> Any:
    """Make a request to the Mistral API.

    Args:
        prompt: The text prompt.
        model: Model ID to use.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.

    Returns:
        Parsed JSON response from the API.

    Raises:
        urllib.error.URLError: If the request fails.
        ValueError: If the response is invalid.
    """
    api_key = _get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    request = urllib.request.Request(
        MISTRAL_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def run_llm(
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    """Run the LLM with the given prompt.

    Args:
        prompt: The text prompt.
        model: Model ID to use (default: mistral-medium-latest).
        max_tokens: Maximum tokens to generate (default: 512).
        temperature: Sampling temperature (default: 0.3).

    Returns:
        The LLM output as a string, or an error message if it fails.
    """
    try:
        response = _make_api_request(prompt, model, max_tokens, temperature)

        if "choices" not in response or not response["choices"]:
            logger.error(f"Invalid API response: {response}")
            return "Error: Invalid API response"

        choice = response["choices"][0]
        content = choice.get("message", {}).get("content", "")

        if not content:
            logger.error(f"Empty response from API: {response}")
            return "Error: Empty response from API"

        return content

    except ValueError as e:
        logger.error(f"Mistral API configuration error: {e}")
        return f"Configuration error: {e}"
    except urllib.error.HTTPError as e:
        logger.error(f"Mistral API HTTP error: {e.code} - {e.reason}")
        return f"API error: HTTP {e.code} - {e.reason}"
    except urllib.error.URLError as e:
        logger.error(f"Mistral API connection error: {e.reason}")
        return f"Connection error: {e.reason}"
    except Exception as e:
        logger.error(f"Error running Mistral API: {e}")
        return f"Error generating text: {e}"
