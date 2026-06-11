import os
import time
from openai import OpenAI


def _get_client() -> OpenAI:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY non trovata nel file .env")
    return OpenAI(api_key=key, base_url="https://api.deepseek.com")


def chat(messages: list[dict], model: str = "deepseek-chat", temperature: float = 0.7, max_tokens: int = 4096) -> str:
    client = _get_client()
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model, messages=messages,
                temperature=temperature, max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
            else:
                raise


def chat_stream(messages: list[dict], model: str = "deepseek-chat", temperature: float = 0.7):
    client = _get_client()
    stream = client.chat.completions.create(
        model=model, messages=messages,
        temperature=temperature, stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
