from groq import Groq
from app.config import settings

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client

def generate(system_prompt: str, user_prompt: str, model: str = "llama-3.1-8b-instant") -> str:
    resp = _get_client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=2048,
    )
    return resp.choices[0].message.content
