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

# fallback models in order of preference
_FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemma-3-27b-it",
    "gemma-3-12b-it"
]

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


def call_gemini(prompt: str, model: str = _FALLBACK_MODELS[0]) -> dict:
    """
    Send a prompt to Gemini/Gemma and return parsed JSON response.

    Args:
        prompt: The fully-formed prompt string.
        model: The model name to use.

    Returns:
        Parsed dict from Gemini's JSON response.

    Raises:
        ValueError: If the response cannot be parsed as JSON.
        RuntimeError: If Gemini returns an error or empty response.
    """
    response = _get_client().models.generate_content(
        model=model,
        contents=prompt,
        config=_GENERATION_CONFIG,
    )

    if not response.text:
        raise RuntimeError(f"Model {model} returned an empty response.")

    try:
        return _clean_json_response(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model {model} response was not valid JSON: {e}\nRaw response: {response.text[:500]}"
        )


async def call_gemini_async(prompt: str, max_retries: int = 2) -> dict:
    """
    Async wrapper for AI calls with multi-model fallback and retry logic.
    Specially handles 429 RESOURCE_EXHAUSTED errors by switching models.
    """
    last_error = None
    
    for model_name in _FALLBACK_MODELS:
        for attempt in range(max_retries + 1):
            try:
                print(f"Calling AI model: {model_name} (Attempt {attempt+1})")
                return await asyncio.to_thread(call_gemini, prompt, model_name)
            except Exception as e:
                last_error = e
                err_msg = str(e).upper()
                
                # Check for Rate Limit (429 / RESOURCE_EXHAUSTED)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) + 1
                        print(f"Rate Limit hit for {model_name}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"Rate Limit exhausted for {model_name}. Falling back to next model...")
                        break # Try next model in _FALLBACK_MODELS
                
                # If it's a structural error (JSON, logic), don't retry, just raise
                if isinstance(e, (ValueError, json.JSONDecodeError)):
                    raise e
                    
                # For other unexpected errors, retry once then move on
                if attempt >= 1: break
                await asyncio.sleep(1)

    raise last_error or RuntimeError("All AI models failed after retries.")
