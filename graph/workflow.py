"""
graph/workflow.py
LangGraph workflow definition wiring together all agents into the
Agentic RAG Research Assistant pipeline.

Flow:
    User Query
       -> Supervisor
       -> Query Rewriter
       -> Parallel: Retriever, Web Research
       -> Verifier
       -> Hallucination Checker
       -> Report Generator
       -> Memory Update
       -> Final Response
"""

from langgraph.graph import END, StateGraph

from agents.hallucination_checker_agent import hallucination_checker_node
from agents.memory_agent import memory_agent_node
from agents.query_rewriter_agent import query_rewriter_node
from agents.report_generator_agent import report_generator_node
from agents.retriever_agent import retriever_node
from agents.supervisor_agent import supervisor_node
from agents.verification_agent import verification_node
from agents.web_research_agent import web_research_node
from graph.state import AgentState
from logger import get_logger

logger = get_logger(__name__)


def _join_after_parallel(state: AgentState) -> AgentState:
    """
    No-op join node that LangGraph uses to synchronize the parallel
    retriever and web-research branches before continuing to verification.
    """
    return state


def build_workflow() -> StateGraph:
    """
    Construct and compile the LangGraph workflow.

    Returns:
        A compiled LangGraph graph ready for `.invoke()`.
    """
    graph = StateGraph(AgentState)

    # ---- Register nodes ----
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("query_rewriter", query_rewriter_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("web_research", web_research_node)
    graph.add_node("join", _join_after_parallel)
    graph.add_node("verifier", verification_node)
    graph.add_node("hallucination_checker", hallucination_checker_node)
    graph.add_node("report_generator", report_generator_node)
    graph.add_node("memory_agent", memory_agent_node)

    # ---- Entry point ----
    graph.set_entry_point("supervisor")

    # Supervisor -> Query Rewriter
    graph.add_edge("supervisor", "query_rewriter")

    # Query Rewriter -> Parallel branches (Retriever + Web Research)
    graph.add_edge("query_rewriter", "retriever")
    graph.add_edge("query_rewriter", "web_research")

    # Both parallel branches converge at "join"
    graph.add_edge("retriever", "join")
    graph.add_edge("web_research", "join")

    # join -> Verifier -> Hallucination Checker -> Report Generator -> Memory -> END
    graph.add_edge("join", "verifier")
    graph.add_edge("verifier", "hallucination_checker")
    graph.add_edge("hallucination_checker", "report_generator")
    graph.add_edge("report_generator", "memory_agent")
    graph.add_edge("memory_agent", END)

    compiled = graph.compile()
    logger.info("LangGraph workflow compiled successfully.")
    return compiled


_workflow_instance = None


def get_workflow():
    """Return a singleton compiled workflow instance."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = build_workflow()
    return _workflow_instance
