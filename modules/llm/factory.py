"""Selects the LLM adapter from LLM_PROVIDER (.env): 'local' (Ollama) or 'huggingface'."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Loads .env from the project root into os.environ, if the file exists
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "local").lower()
    if provider == "huggingface":
        from modules.llm.hf_api import HFClient
        return HFClient()
    if provider == "local":
        from modules.llm.local import OllamaClient
        return OllamaClient()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (use 'local' or 'huggingface')")