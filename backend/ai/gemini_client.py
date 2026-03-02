"""
Gemini API Client — wraps google-genai for all AI calls.
All Gemini inference flows through this module.
"""

import json
import re
import os
import asyncio
from typing import Any, cast
import google.genai as genai
from google.genai import types as genai_types
from dotenv import load_dotenv

load_dotenv()

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Single model used for all tasks
_MODEL = "gemini-2.5-flash"

# Lazy-initialized client — created on first use so that importing this module
# does NOT raise an error when GEMINI_API_KEY is not yet set (e.g. during tests
# or cold import in development with no .env file present).
_client: Any = None


def _get_client() -> Any:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        _client = genai.Client(api_key=api_key)
    return _client


_GENERATION_CONFIG = genai_types.GenerateContentConfig(
    temperature=0.1,       # Low temp for consistent structured output
    top_p=0.95,
    max_output_tokens=8192,
    safety_settings=[
        genai_types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="BLOCK_NONE",
        ),
        genai_types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="BLOCK_NONE",
        ),
        genai_types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="BLOCK_NONE",
        ),
        genai_types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_NONE",
        ),
    ],
)


def _clean_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON from Gemini response."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    return json.loads(cleaned)


def call_gemini(prompt: str) -> dict:
    """
    Send a prompt to Gemini and return parsed JSON response.

    Args:
        prompt: The fully-formed prompt string.

    Returns:
        Parsed dict from Gemini's JSON response.

    Raises:
        ValueError: If the response cannot be parsed as JSON.
        RuntimeError: If Gemini returns an error or empty response.
    """
    response = _get_client().models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=_GENERATION_CONFIG,
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        return _clean_json_response(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini response was not valid JSON: {e}\nRaw response: {response.text[:500]}"
        )


async def call_gemini_async(prompt: str, max_retries: int = 3) -> dict:
    """
    Async wrapper for Gemini calls with built-in retry logic (exponential backoff).
    Specially handles 429 RESOURCE_EXHAUSTED errors for the Free Tier.
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            fn: Any = cast(Any, call_gemini)
            return await asyncio.to_thread(fn, prompt)
        except Exception as e:
            last_error = e
            err_msg = str(e)
            
            # Check for Rate Limit (429)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                wait_time = (2 ** attempt) + 1  # 2, 3, 5, 9 seconds...
                print(f"Gemini Rate Limit hit. Retrying in {wait_time}s (Attempt {attempt+1}/{max_retries+1})...")
                await asyncio.sleep(wait_time)
                continue
            
            # If it's a structural error (JSON, logic), don't retry, just raise
            if isinstance(e, (ValueError, json.JSONDecodeError)):
                raise e
                
            # For other unexpected errors, retry once then fail
            if attempt >= 1: break
            await asyncio.sleep(1)

    raise last_error or RuntimeError("Gemini call failed after retries.")
