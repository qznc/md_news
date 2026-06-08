# Mistral API Documentation

This document describes how to use the Mistral AI REST API for LLM operations in the md-news project.

## Overview

The md-news project uses the Mistral REST API for LLM operations via `lib/llm.py`. The implementation uses Python builtins (`urllib.request`, `json`) to make HTTP requests directly to the API.

## Authentication

### Prerequisites

1. Create an account at [console.mistral.ai](https://console.mistral.ai)
2. Generate an API key in the "API Keys" section
3. Store the key in a `.env` file at the project root:

```bash
# .env file
MISTRAL_API_KEY=your-api-key-here
```

The API key is read from the `.env` file by `lib/llm.py`. Alternatively, you can set it as an environment variable.

## REST API Usage

### Base URL
```
https://api.mistral.ai/v1/
```

### Chat Completion Endpoint

**POST** `/v1/chat/completions`

The primary endpoint for text generation.

#### Request Headers
```
Authorization: Bearer ${MISTRAL_API_KEY}
Content-Type: application/json
```

#### Request Body
```json
{
  "model": "mistral-medium-latest",
  "messages": [
    {"role": "user", "content": "Your prompt here"}
  ],
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.9
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | Yes | - | Model ID (see Available Models below) |
| `messages` | array | Yes | - | List of message objects with `role` and `content` |
| `max_tokens` | integer | No | varies | Maximum tokens to generate |
| `temperature` | number | No | varies | Sampling temperature (0.0-1.0) |
| `top_p` | number | No | 1.0 | Nucleus sampling (0.0-1.0) |
| `stop` | string/array | No | null | Stop sequence(s) |
| `stream` | boolean | No | false | Enable streaming |
| `random_seed` | integer | No | null | Random seed for reproducibility |

#### cURL Example
```bash
curl https://api.mistral.ai/v1/chat/completions \
  -X POST \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "mistral-medium-latest",
    "messages": [{"role": "user", "content": "Summarize this article: ..."}],
    "max_tokens": 256,
    "temperature": 0.3
  }'
```

#### Response
```json
{
  "id": "cmpl-123456789",
  "object": "chat.completion",
  "created": 1702256327,
  "model": "mistral-medium-latest",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Generated text here..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 50,
    "total_tokens": 75
  }
}
```

## Available Models

### List Models

```bash
curl https://api.mistral.ai/v1/models \
  -H 'Authorization: Bearer YOUR_API_KEY'
```

### Common Model IDs (as of June 2026)

| Model ID | Description | Max Context |
|----------|-------------|--------------|
| `mistral-small-latest` | Fast, cost-effective | 32K |
| `mistral-medium-latest` | Balanced speed/cost | 32K |
| `mistral-large-latest` | Most capable | 128K |
| `mistral-embed` | Embedding model | - |

> **Note:** Model names include `-latest` suffix for automatic version updates. For pinned versions, use specific dates like `mistral-medium-2024-05-20`.

## Integration with md-news

The `lib/llm.py` module uses the Mistral REST API with Python builtins (no external dependencies).

### Usage in Project Code

```python
from lib.llm import run_llm

# Basic usage with defaults
result = run_llm("Write a summary of this article...")

# With custom parameters
result = run_llm(
    "Analyze this text...",
    model="mistral-large-latest",
    max_tokens=1024,
    temperature=0.5
)
```

### Configuration

The `run_llm()` function accepts:
- `prompt` (required): The text prompt
- `model` (default: `mistral-medium-latest`): Model ID
- `max_tokens` (default: 512): Maximum tokens to generate
- `temperature` (default: 0.3): Sampling temperature
- `thinking` (default: `False`): Enable reasoning effort. When True, uses `reasoning_effort="high"` and logs thinking traces (never returned in the output).

### Reasoning/Thinking Support

The implementation supports Mistral's reasoning feature via the `thinking` parameter:

When `thinking=True`:
- Sets `reasoning_effort="high"` in the API request
- Handles the special response format (list of ThinkChunk/TextChunk objects)
- Extracts and logs thinking traces using the standard logger
- Returns only the final answer text (never the thinking content)

## Comparison: vibe CLI vs Mistral API

| Feature | vibe CLI | Mistral API |
|---------|----------|--------------|
| Offline capability | Yes (local models) | No (cloud only) |
| Cost | Free (local inference) | Paid (per-token) |
| Model selection | Limited to local | Full model catalog |
| Latency | Higher (local) | Lower (cloud) |
| Setup | Install vibe + models | Just API key |
| Python integration | Subprocess | urllib (builtins) |
| Streaming | Yes | Yes |
| Context length | Limited by local | Up to 128K |

## Best Practices

1. **Error Handling**: API errors are handled gracefully with user-friendly messages
2. **Rate Limiting**: Mistral API has rate limits; the timeout is set to 120 seconds
3. **Model Selection**: Use `mistral-medium-latest` for most tasks, `mistral-large-latest` for complex reasoning
4. **Temperature**: Lower values (0.3-0.5) for deterministic outputs, higher (0.7-0.9) for creativity
5. **Context**: Keep prompts concise; use `max_tokens` to control output length

## Useful Links

- [Mistral API Documentation](https://docs.mistral.ai/api)
- [Model Overview](https://docs.mistral.ai/models)
- [Console](https://console.mistral.ai) - Get API keys and manage projects
