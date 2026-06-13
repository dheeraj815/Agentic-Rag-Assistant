"""
utils/llm_clients.py
Factory functions for constructing LLM clients (Groq primary, Anthropic optional).
"""

from functools import lru_cache
from typing import Optional

from langchain_groq import ChatGroq

from config import settings
from logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=4)
def get_groq_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> ChatGroq:
    """
    Return a cached ChatGroq LLM client (primary LLM for all agents).

    Args:
        model: Groq model name (defaults to settings.GROQ_MODEL).
        temperature: Sampling temperature (defaults to settings.GROQ_TEMPERATURE).

    Returns:
        A configured ChatGroq instance.

    Raises:
        ValueError: If GROQ_API_KEY is not configured.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. Please configure it in your .env file."
        )

    model = model or settings.GROQ_MODEL
    temperature = temperature if temperature is not None else settings.GROQ_TEMPERATURE

    logger.debug("Initializing ChatGroq client (model=%s, temperature=%s)", model, temperature)
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=model,
        temperature=temperature,
    )


@lru_cache(maxsize=2)
def get_anthropic_llm(model: str = "claude-sonnet-4-6"):
    """
    Return a cached ChatAnthropic client for OPTIONAL verification tasks.

    Returns None if ANTHROPIC_API_KEY is not configured, allowing callers
    to gracefully skip optional verification.

    Args:
        model: Anthropic model name.

    Returns:
        A ChatAnthropic instance, or None if not configured.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.info("ANTHROPIC_API_KEY not set; optional Claude verification disabled.")
        return None

    try:
        from langchain_anthropic import ChatAnthropic

        logger.debug("Initializing ChatAnthropic client (model=%s)", model)
        return ChatAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            model=model,
            temperature=0,
        )
    except Exception:
        logger.exception("Failed to initialize Anthropic client; continuing without it.")
        return None
