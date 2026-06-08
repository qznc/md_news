#!/usr/bin/env python3
"""LLM utilities for md-news."""

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

# Models that support reasoning_effort
REASONING_MODELS = ["mistral-small-latest", "mistral-medium-3.5", "mistral-medium-3-5"]


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


def _make_api_request(
    prompt: str, model: str, max_tokens: int, temperature: float, thinking: bool = False
) -> Any:
    """Make a request to the Mistral API.

    Args:
        prompt: The text prompt.
        model: Model ID to use.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        thinking: Whether to enable reasoning_effort (default: False).

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

    # Add reasoning_effort if thinking is enabled
    if thinking:
        payload["reasoning_effort"] = "high"

    request = urllib.request.Request(
        MISTRAL_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def run_llm_mistral(
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    thinking: bool = False,
) -> str:
    """Run the LLM with the given prompt.

    Args:
        prompt: The text prompt.
        model: Model ID to use (default: mistral-medium-latest).
        max_tokens: Maximum tokens to generate (default: 512).
        temperature: Sampling temperature (default: 0.3).
        thinking: Whether to enable reasoning_effort (default: False).
                  When True, thinking traces are logged but never returned.
                  Automatically uses a reasoning-compatible model if needed.

    Returns:
        The LLM output as a string, or an error message if it fails.
    """
    try:
        # If thinking is enabled and current model doesn't support reasoning, switch to a compatible one
        effective_model = model
        if thinking and model not in REASONING_MODELS:
            effective_model = "mistral-medium-3.5"
            logger.info(
                f"Switching from {model} to {effective_model} for reasoning support"
            )

        response = _make_api_request(
            prompt, effective_model, max_tokens, temperature, thinking
        )

        if "choices" not in response or not response["choices"]:
            logger.error(f"Invalid API response: {response}")
            return "Error: Invalid API response"

        choice = response["choices"][0]
        content = choice.get("message", {}).get("content", "")

        if not content:
            logger.error(f"Empty response from API: {response}")
            return "Error: Empty response from API"

        # Handle reasoning response format
        if thinking and isinstance(content, list):
            # Extract thinking and final answer from chunks
            thinking_text = ""
            final_text = ""

            for chunk in content:
                if isinstance(chunk, dict):
                    chunk_type = chunk.get("type", "")
                    if chunk_type == "thinking":
                        # Extract thinking content
                        chunk_thinking = chunk.get("thinking", [])
                        if isinstance(chunk_thinking, list):
                            for inner in chunk_thinking:
                                if (
                                    isinstance(inner, dict)
                                    and inner.get("type") == "text"
                                ):
                                    thinking_text += inner.get("text", "")
                    elif chunk_type == "text":
                        final_text += chunk.get("text", "")
                elif isinstance(content, str):
                    final_text = content

            # Log thinking traces
            if thinking_text:
                logger.info(f"LLM thinking: {thinking_text}")

            return final_text
        elif isinstance(content, list):
            # Handle non-thinking list format (shouldn't happen but be safe)
            logger.error(f"Unexpected list content without thinking: {content}")
            return "Error: Unexpected response format"

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


def run_llm_openrouter(prompt: str, thinking: bool = False) -> str:
    """Openrouter API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not found. Set it in environment variable. "
            "Get one at https://openrouter.ai"
        )
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": DEFAULT_MAX_TOKENS,
        "reasoning": {"enabled": thinking},
    }
    logger.debug(f"Prepared Openrouter API request data: {data}")
    req = urllib.request.Request(
        url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST"
    )
    logger.debug(f"Sending Openrouter API request {repr(req)}")
    with urllib.request.urlopen(req, timeout=60) as response:
        res = json.loads(response.read().decode("utf-8"))
    res_model = res.get("model", "unknown")
    res_provider = res.get("provider", "unknown")
    logger.debug(f"Openrouter API response from {res_model} (provider: {res_provider})")
    res_usage = res.get("usage", {})
    res_prompt_tokens = res_usage.get("prompt_tokens", "unknown")
    res_completion_tokens = res_usage.get("completion_tokens", "unknown")
    logger.debug(f"prompt={res_prompt_tokens}, completion={res_completion_tokens}")
    return res["choices"][0]["message"]["content"]


run_llm = run_llm_openrouter
