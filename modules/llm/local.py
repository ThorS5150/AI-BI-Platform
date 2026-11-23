"""Adapter for a local LLM served by Ollama (default: http://localhost:11434)."""
import os
import requests

#DEFAULT_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b-instruct")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct")
DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


class OllamaClient:
    def __init__(self, model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST, timeout: int = 120):
        self.model = model
        self.url = f"{host.rstrip('/')}/api/chat"
        self.timeout = timeout

    def chat(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 300},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        response = requests.post(self.url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()["message"]["content"]