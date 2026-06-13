"""
utils/verification_claude.py
OPTIONAL secondary verification using Anthropic's Claude model.
Only active if ANTHROPIC_API_KEY is configured; otherwise gracefully skipped.
"""

from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from logger import get_logger
from utils.llm_clients import get_anthropic_llm

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an independent fact-checking reviewer.
Given a CONTEXT and an ANSWER, briefly assess (in 1-3 sentences) whether the
answer appears consistent with the context, noting any obvious inconsistencies.
Be concise and neutral.
"""


def claude_verify(context: str, answer: str) -> Optional[str]:
    """
    Run an optional secondary verification pass using Claude.

    Args:
        context: The retrieved context used to generate the answer.
        answer: The generated answer to review.

    Returns:
        A short textual review from Claude, or None if Claude is not configured
        or the call fails (callers should treat None as "skipped").
    """
    llm = get_anthropic_llm()
    if llm is None:
        return None

    try:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"Context:\n{context[:6000]}\n\nAnswer:\n{answer}\n\nReview:"
            ),
        ]
        response = llm.invoke(messages)
        review = response.content.strip()
        logger.info("Claude verification completed.")
        return review
    except Exception:
        logger.exception("Optional Claude verification failed; skipping.")
        return None
