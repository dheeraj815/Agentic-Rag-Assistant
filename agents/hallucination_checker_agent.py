"""
agents/hallucination_checker_agent.py
Hallucination Checker Agent: generates a draft answer grounded in the
context, then scores it for hallucination risk and confidence.
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState
from logger import get_logger
from utils.llm_clients import get_groq_llm

logger = get_logger(__name__)

DRAFT_SYSTEM_PROMPT = """You are a research assistant. Answer the user's query using ONLY
the information provided in the context below. Be accurate, concise, and well-organized.
If the context does not fully answer the query, say so explicitly within the answer.
Do not invent facts not present in the context.
"""

CHECK_SYSTEM_PROMPT = """You are the Hallucination Checker Agent.

Given a CONTEXT and a DRAFT ANSWER, evaluate how well the draft answer is grounded
in the context. Identify any claims in the draft that are NOT supported by the context
(potential hallucinations).

Respond with ONLY a JSON object in this exact format:
{
  "hallucination_score": <float 0.0-1.0, where 0.0 = fully grounded, 1.0 = completely unsupported>,
  "confidence_score": <float 0.0-1.0, representing overall confidence the answer is correct and well-supported>,
  "flags": ["<short description of unsupported claim>", ...]
}

If the draft is fully supported by the context, return an empty "flags" list and a low hallucination_score.
"""


def hallucination_checker_node(state: AgentState) -> AgentState:
    """
    Hallucination Checker node: generates `final_answer`, `hallucination_score`,
    `confidence_score`, and `hallucination_flags`.
    """
    query = state.get("rewritten_query") or state.get("original_query", "")

    rag_context = state.get("rag_context", "")
    web_context = state.get("web_context", "")
    combined_context = "\n\n".join(filter(None, [rag_context, web_context]))

    llm = get_groq_llm()

    # ---- Step 1: Generate draft answer ----
    try:
        if combined_context.strip():
            draft_messages = [
                SystemMessage(content=DRAFT_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Context:\n{combined_context[:10000]}\n\n"
                        f"Query: {query}\n\nAnswer:"
                    )
                ),
            ]
        else:
            draft_messages = [
                SystemMessage(
                    content=(
                        "You are a helpful research assistant. No external context was "
                        "available, so answer using your general knowledge and clearly "
                        "state that no specific sources were consulted."
                    )
                ),
                HumanMessage(content=f"Query: {query}\n\nAnswer:"),
            ]

        draft_response = llm.invoke(draft_messages)
        draft_answer = draft_response.content.strip()

    except Exception as exc:
        logger.exception("Failed to generate draft answer.")
        return {
            **state,
            "final_answer": "I encountered an error while generating an answer. Please try again.",
            "hallucination_score": 1.0,
            "confidence_score": 0.0,
            "hallucination_flags": [f"Draft generation failed: {exc}"],
            "errors": [f"HallucinationCheckerAgent (draft) error: {exc}"],
        }

    # ---- Step 2: Score the draft for hallucinations ----
    if not combined_context.strip():
        # No context to ground against; assign neutral/cautious scores
        return {
            **state,
            "final_answer": draft_answer,
            "hallucination_score": 0.5,
            "confidence_score": 0.4,
            "hallucination_flags": ["No retrieved context was available to verify this answer."],
        }

    try:
        check_messages = [
            SystemMessage(content=CHECK_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Context:\n{combined_context[:10000]}\n\n"
                    f"Draft Answer:\n{draft_answer}\n\n"
                    "Evaluate:"
                )
            ),
        ]
        check_response = llm.invoke(check_messages)
        content = check_response.content.strip()

        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        result = json.loads(content)
        hallucination_score = float(result.get("hallucination_score", 0.3))
        confidence_score = float(result.get("confidence_score", 0.7))
        flags = result.get("flags", [])

        # Clamp values to [0, 1]
        hallucination_score = max(0.0, min(1.0, hallucination_score))
        confidence_score = max(0.0, min(1.0, confidence_score))

        logger.info(
            "Hallucination check: score=%.2f, confidence=%.2f, flags=%d",
            hallucination_score, confidence_score, len(flags),
        )

        return {
            **state,
            "final_answer": draft_answer,
            "hallucination_score": hallucination_score,
            "confidence_score": confidence_score,
            "hallucination_flags": flags,
        }

    except Exception as exc:
        logger.exception("Hallucination scoring failed; using default moderate scores.")
        return {
            **state,
            "final_answer": draft_answer,
            "hallucination_score": 0.4,
            "confidence_score": 0.6,
            "hallucination_flags": [],
            "errors": [f"HallucinationCheckerAgent (scoring) error: {exc}"],
        }
