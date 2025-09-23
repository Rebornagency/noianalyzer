"""Utility wrappers around OpenAI chat completion with retry and timeout.

The goal is to give all application modules a single integration
point that already handles:
    • API key lookup via config.get_openai_api_key()
    • Graceful retries on RateLimit / transient network errors
    • Request timeout
    • Optional JSON schema enforcement (future-proof)

This file purposefully has **no** external dependencies other than
`openai` itself to avoid bloat.
"""
from __future__ import annotations

import logging
import time
from typing import Any, List, Dict, Union

import openai
from openai import OpenAI
# Import specific error types from openai
from openai import RateLimitError, APIConnectionError, APIError

from config import get_openai_api_key

logger = logging.getLogger(__name__)

# Default retry/back-off parameters
_OPENAI_MAX_RETRIES = 3
_OPENAI_BACKOFF_SECONDS = 2
_OPENAI_TIMEOUT = 30  # seconds

# Initialise a singleton client – OpenAI lib is thread-safe for basic use-cases
_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=get_openai_api_key())
    return _client

def chat_completion(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.1,
    max_tokens: int | None = None,
    **kwargs: Any,
) -> str:
    """Safely call the OpenAI ChatCompletion endpoint.

    On success returns the *content* string of the first choice.
    On failure raises the encountered exception (caller may catch).
    """
    client = _get_client()
    attempt = 0
    backoff = _OPENAI_BACKOFF_SECONDS

    # Convert messages to the correct format
    formatted_messages = []
    for msg in messages:
        if "role" in msg and "content" in msg:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})
        else:
            # Handle any malformed messages
            continue

    while True:
        attempt += 1
        try:
            response = client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=_OPENAI_TIMEOUT,
                **kwargs,
            )
            return response.choices[0].message.content.strip()
        except (RateLimitError, APIConnectionError, APIError, TimeoutError) as e:
            if attempt >= _OPENAI_MAX_RETRIES:
                logger.error("OpenAI chat completion failed after %s attempts: %s", attempt, e)
                raise
            logger.warning("OpenAI error (%s). Retry %s/%s after %ss", type(e).__name__, attempt, _OPENAI_MAX_RETRIES, backoff)
            time.sleep(backoff)
            backoff *= 2  # Exponential back-off, capped implicitly by retry count
        except Exception:
            # Unknown error – do not retry
            raise