"""Adapter for a hosted LLM via the Hugging Face Inference API (chat completion).

Token comes from HF_TOKEN: in .env locally, as a Space secret when deployed.
Never commit the token.
"""
import os

from huggingface_hub import InferenceClient

DEFAULT_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")


class HFClient:
    def __init__(self, model: str = DEFAULT_MODEL, token: str | None = None, timeout: int = 120):
        self.model = model
        self.client = InferenceClient(model=model, token=token or os.getenv("HF_TOKEN"), timeout=timeout)

    def chat(self, system: str, user: str) -> str:
        response = self.client.chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=300,
            temperature=0.01,  # 0 is rejected by some providers
        )
        return response.choices[0].message.content