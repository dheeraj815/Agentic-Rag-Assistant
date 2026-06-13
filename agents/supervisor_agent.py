"""
agents/supervisor_agent.py
Supervisor Agent: analyzes the incoming query and decides the routing
strategy (use RAG, use web search, both, or answer directly).
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import AgentState
from logger import get_logger
from rag.retriever import has_indexed_documents
from utils.llm_clients import get_groq_llm

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Supervisor Agent of a research assistant system.
Given a user's query, decide which information sources are needed to answer it well.

Respond with ONLY a JSON object in this exact format:
{
  "use_rag": <true|false>,
  "use_web": <true|false>,
  "reasoning": "<short reason>"
}

Guidelines:
- use_rag: true if the query likely relates to uploaded documents, or if document context could help.
- use_web: true if the query needs current/external/factual information beyond any documents (news, recent events, general knowledge lookups, comparisons).
- For simple greetings, chit-chat, or meta questions about the assistant itself, set both to false.
- If unsure, prefer setting both to true for thorough research.
"""


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor node: determines routing for the rest of the pipeline.

    Updates state with:
        - use_rag (bool)
        - use_web (bool)
        - route_decision (str)
        - errors (list, appended on failure)
    """
    query = state.get("original_query", "")
    docs_available = has_indexed_documents()

    try:
        llm = get_groq_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"User query: {query}\n"
                    f"Documents currently indexed in RAG store: {docs_available}"
                )
            ),
        ]
        response = llm.invoke(messages)
        content = response.content.strip()

        # Strip potential markdown code fences
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        decision = json.loads(content)
        use_rag = bool(decision.get("use_rag", False)) and docs_available
        use_web = bool(decision.get("use_web", False))

        # Fallback: if nothing is selected, default to web search for safety
        if not use_rag and not use_web:
            use_web = True

        if use_rag and use_web:
            route_decision = "rag_and_web"
        elif use_rag:
            route_decision = "rag_only"
        elif use_web:
            route_decision = "web_only"
        else:
            route_decision = "direct"

        logger.info(
            "Supervisor decision for query '%s': use_rag=%s, use_web=%s, route=%s",
            query, use_rag, use_web, route_decision,
        )

        return {
            **state,
            "use_rag": use_rag,
            "use_web": use_web,
            "route_decision": route_decision,
        }

    except Exception as exc:
        logger.exception("Supervisor agent failed; defaulting to rag_and_web (if docs available).")
        use_rag = docs_available
        use_web = True
        return {
            **state,
            "use_rag": use_rag,
            "use_web": use_web,
            "route_decision": "rag_and_web" if use_rag else "web_only",
            "errors": [f"SupervisorAgent error: {exc}"],
        }
