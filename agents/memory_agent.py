"""
agents/memory_agent.py
Memory Agent: persists the final conversation turn and report metadata
to the SQLite-backed conversation memory and reports table.
"""

from database.models import ReportRecord, add_report_record
from graph.state import AgentState
from logger import get_logger
from memory.conversation_memory import ConversationMemory

logger = get_logger(__name__)


def memory_agent_node(state: AgentState) -> AgentState:
    """
    Memory Agent node: stores the user query and assistant answer in
    conversation memory, and records report metadata.

    Populates `memory_updated` (bool).
    """
    session_id = state.get("session_id", "default")

    try:
        memory = ConversationMemory(session_id=session_id)

        original_query = state.get("original_query", "")
        final_answer = state.get("final_answer", "")

        memory.add_user_message(original_query)
        memory.add_assistant_message(
            final_answer,
            metadata={
                "confidence_score": state.get("confidence_score"),
                "hallucination_score": state.get("hallucination_score"),
                "report_file_path": state.get("report_file_path"),
                "route_decision": state.get("route_decision"),
            },
        )

        report_path = state.get("report_file_path", "")
        if report_path:
            add_report_record(
                ReportRecord(
                    session_id=session_id,
                    query=original_query,
                    file_path=report_path,
                    confidence_score=state.get("confidence_score"),
                    hallucination_score=state.get("hallucination_score"),
                )
            )

        logger.info("Memory updated for session '%s'.", session_id)

        return {**state, "memory_updated": True}

    except Exception as exc:
        logger.exception("Memory agent failed.")
        return {**state, "memory_updated": False, "errors": [f"MemoryAgent error: {exc}"]}
