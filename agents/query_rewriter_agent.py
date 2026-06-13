"""
agents/query_rewriter_agent.py
Query Rewriter Agent: rewrites the user's query into a clear, standalone,
search-optimized query using conversation context.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState
from logger import get_logger
from memory.conversation_memory import ConversationMemory
from utils.llm_clients import get_groq_llm

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Query Rewriter Agent in a research assistant pipeline.

Your job: rewrite the user's latest query into a clear, self-contained, search-optimized
query that:
- Resolves pronouns and references using the conversation context (e.g. "it", "that paper").
- Is specific and unambiguous.
- Removes conversational filler ("can you please", "I was wondering").
- Preserves the original intent and all important details.

Respond with ONLY the rewritten query text. No explanations, no quotes, no extra formatting.
"""


def query_rewriter_node(state: AgentState) -> AgentState:
    """
    Query Rewriter node: produces `rewritten_query` and `conversation_context`.

    Falls back to the original query on any failure.
    """
    query = state.get("original_query", "")
    session_id = state.get("session_id", "default")

    try:
        memory = ConversationMemory(session_id=session_id)
        context = memory.get_recent_context_summary(limit=6)

        if not context:
            logger.info("No conversation context available; using original query as-is.")
            return {
                **state,
                "rewritten_query": query,
                "conversation_context": "",
            }

        llm = get_groq_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Conversation history:\n{context}\n\n"
                    f"Latest user query: {query}\n\n"
                    "Rewritten standalone query:"
                )
            ),
        ]
        response = llm.invoke(messages)
        rewritten = response.content.strip().strip('"').strip()

        if not rewritten:
            rewritten = query

        logger.info("Query rewritten: '%s' -> '%s'", query, rewritten)

        return {
            **state,
            "rewritten_query": rewritten,
            "conversation_context": context,
        }

    except Exception as exc:
        logger.exception("Query rewriter failed; falling back to original query.")
        return {
            **state,
            "rewritten_query": query,
            "conversation_context": "",
            "errors": [f"QueryRewriterAgent error: {exc}"],
        }
