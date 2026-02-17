"""
Centralized LLM factory for Stereo Sonic Assistant.
Switches between local Ollama and API-based providers (Gemini/OpenAI) via LOCAL_LLM env flag.
"""

import os
from typing import Optional

# Re-export for consumers that need provider name for logging/status
def get_llm_provider() -> str:
    """Get the configured LLM provider name from environment (local, gemini, or openai)."""
    if is_local_llm():
        return "local"
    return os.getenv("LLM_PROVIDER", "gemini").lower()


def is_local_llm() -> bool:
    """Return True when LOCAL_LLM env is set to a truthy value (e.g. True, true, 1, yes)."""
    val = os.getenv("LOCAL_LLM", "").strip().lower()
    return val in ("true", "1", "yes")


def create_llm(temperature: float = 0.9, for_tools: bool = False):
    """
    Create a LangChain chat model for text/chat use.
    When LOCAL_LLM is True uses Ollama; otherwise uses LLM_PROVIDER (gemini/openai).
    """
    if is_local_llm():
        from langchain_ollama import ChatOllama
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        kwargs = {
            "model": model,
            "base_url": base_url,
            "temperature": temperature,
        }
        if for_tools:
            # Per LangChain Ollama docs: validate model on init when using tools (set OLLAMA_VALIDATE_MODEL_ON_INIT=false to disable)
            val = os.getenv("OLLAMA_VALIDATE_MODEL_ON_INIT", "true").strip().lower()
            kwargs["validate_model_on_init"] = val in ("true", "1", "yes")
            # Do NOT set format="json" here: it makes the model return tool-call JSON as content instead of using native tool_calls, so no tool runs
        return ChatOllama(**kwargs)
    # API-based providers
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=api_key,
        )
    # Default: Gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        google_api_key=api_key,
    )


def create_vision_llm():
    """
    Create a LangChain chat model suitable for image input (vision).
    When LOCAL_LLM is True uses Ollama vision model; otherwise uses Gemini vision.
    """
    if is_local_llm():
        from langchain_ollama import ChatOllama
        model = os.getenv("OLLAMA_VISION_MODEL", "llava")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0.7,
        )
    from langchain_google_genai import ChatGoogleGenerativeAI
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        google_api_key=api_key,
    )
