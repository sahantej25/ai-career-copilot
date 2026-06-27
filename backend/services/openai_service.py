import json
from typing import Any
from openai import AsyncOpenAI
from config import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def chat_json(system: str, user: str, temperature: float = 0.3) -> dict[str, Any]:
    """Call OpenAI and parse the JSON response reliably."""
    client = get_client()
    response = await client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


async def chat_text(system: str, user: str, temperature: float = 0.5) -> str:
    """Call OpenAI and return plain text."""
    client = get_client()
    response = await client.chat.completions.create(
        model=settings.openai_model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""
