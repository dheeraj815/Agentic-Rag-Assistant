"""
agents/verification_agent.py
Verification Agent: checks whether the gathered context (RAG + web) is
sufficient to answer the query, and notes gaps.
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState
from logger import get_logger
from utils.llm_clients import get_groq_llm

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Verification Agent in a research assistant pipeline.

Given a user query and the gathered context (from documents and/or web search),
assess whether the context is SUFFICIENT to produce an accurate, well-supported answer.

Respond with ONLY a JSON object in this exact format:
{
  "is_sufficient": <true|false>,
  "notes": "<1-2 sentence assessment of coverage and any gaps>"
}
"""


def verification_node(state: AgentState) -> AgentState:
    """
    Verification node: populates `is_sufficient` and `verification_notes`.
    """
    query = state.get("rewritten_query") or state.get("original_query", "")

    rag_context = state.get("rag_context", "")
    web_context = state.get("web_context", "")
    combined_context = "\n\n".join(filter(None, [rag_context, web_context]))

    if not combined_context.strip():
        logger.info("No context available for verification; marking as insufficient.")
        return {
            **state,
            "is_sufficient": False,
            "verification_notes": "No retrieved context available from documents or web search.",
        }

    try:
        llm = get_groq_llm()
        # Truncate context to avoid excessive token usage
        truncated_context = combined_context[:8000]

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"User query: {query}\n\n"
                    f"Gathered context:\n{truncated_context}\n\n"
                    "Assess sufficiency:"
                )
            ),
        ]
        response = llm.invoke(messages)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        result = json.loads(content)
        is_sufficient = bool(result.get("is_sufficient", True))
        notes = result.get("notes", "")

        logger.info("Verification result: is_sufficient=%s, notes='%s'", is_sufficient, notes)

        return {
            **state,
            "is_sufficient": is_sufficient,
            "verification_notes": notes,
        }

    except Exception as exc:
        logger.exception("Verification agent failed; assuming context is sufficient.")
        return {
            **state,
            "is_sufficient": True,
            "verification_notes": "Verification step encountered an error; proceeding with available context.",
            "errors": [f"VerificationAgent error: {exc}"],
        }
