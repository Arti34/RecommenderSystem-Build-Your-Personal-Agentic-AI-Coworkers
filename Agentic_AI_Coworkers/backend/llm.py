"""Optional local Ollama summarization; transparent fallback if unavailable."""
import os


def generate(prompt: str, system: str, max_tokens: int = 180) -> str | None:
    if os.getenv("USE_OLLAMA", "0") != "1":
        return None
    try:
        from ollama import Client
        client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"), timeout=65)
        result = client.chat(
            model=os.getenv("OLLAMA_MODEL", "qwen3:1.7b"),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            think=False,
            options={"num_predict": max_tokens, "num_ctx": 2048, "temperature": 0.2},
        )
        return (result.message.content or "").strip() or None
    except Exception:
        return None
