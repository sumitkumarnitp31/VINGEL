"""Lightweight Gemini REST API client using httpx."""
import json
import re
import httpx
from backend.core.config import GEMINI_API_KEY, GEMINI_MODEL

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def generate_json(prompt: str, timeout: float = 15.0) -> dict | None:
    """Call Gemini generateContent REST API and parse the JSON response. Returns None on failure."""
    try:
        url = _ENDPOINT.format(model=GEMINI_MODEL)
        resp = httpx.post(
            url,
            params={"key": GEMINI_API_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        raw = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except Exception:
        return None

