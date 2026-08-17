"""
Thin wrapper around the Gemini API so agents don't repeat boilerplate.
Reads GEMINI_API_KEY from environment (.env file).
"""
import os
import re
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not found. Create a .env file with:\n"
                "GEMINI_API_KEY=your_key_here"
            )
        _client = genai.Client(api_key=api_key)
    return _client


def call_agent(system_prompt: str, user_prompt: str, model: str = "gemini-3.5-flash",
                max_retries: int = 4) -> str:
    """Send a single-turn request to Gemini and return plain text.
    Retries temporary 429/503 errors, but stops on exhausted daily quota."""
    client = get_client()
    last_error = None

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.8,
                },
            )
            return response.text.strip()
        except genai_errors.ServerError as e:
            last_error = e
            wait = 2 ** attempt  # 1, 2, 4, 8 seconds
            print(f"    (model overloaded, retrying in {wait}s... attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)
        except genai_errors.ClientError as e:
            # ClientError also covers permanent errors, so only retry HTTP 429.
            status_code = getattr(e, "code", None) or getattr(e, "status_code", None)
            if status_code != 429 and "429" not in str(e):
                raise

            error_text = str(e)
            daily_quota_markers = (
                "PerDay",
                "per day",
                "daily quota",
                "GenerateRequestsPerDay",
            )
            if any(marker.lower() in error_text.lower() for marker in daily_quota_markers):
                raise RuntimeError(
                    "Gemini's daily request quota is exhausted. "
                    "Wait for the quota to reset, then run the command again."
                ) from e

            last_error = e
            # Google may include a suggested delay such as "retry in 12.5s".
            match = re.search(r"retry(?:ing)?\s+in\s+([0-9.]+)s", error_text, re.IGNORECASE)
            wait = float(match.group(1)) if match else 2 ** attempt
            wait = min(wait, 60.0)
            print(
                f"    (rate limited, retrying in {wait:g}s... "
                f"attempt {attempt + 1}/{max_retries})"
            )
            time.sleep(wait)

    raise last_error
