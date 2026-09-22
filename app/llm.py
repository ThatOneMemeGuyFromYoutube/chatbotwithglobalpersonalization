from __future__ import annotations

import httpx

from .config import settings

BASE_SYSTEM = """
You are the shared global personality of this chatbot.
Be helpful, respectful, playful when the user is playful, and honest about uncertainty.
Never claim to remember private information about a user unless it is present in the current conversation.
Do not request sensitive personal data unless it is essential to the task.
""".strip()

async def generate(messages: list[dict[str, str]], adapter: dict) -> str:
    system = BASE_SYSTEM + "\n\nGlobal personality adapter:\n" + adapter.get(
        "system_addendum",
        "Be clear, warm, natural, and adapt the amount of detail to the user's request."
    )
    payload = {
        "model": settings.llama_model,
        "messages": [{"role": "system", "content": system}, *messages],
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 20,
        "stream": False,
    }
    url = settings.llama_base_url.rstrip("/") + "/v1/chat/completions"
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    return data["choices"][0]["message"]["content"]
