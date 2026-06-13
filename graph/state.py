"""
graph/state.py
Shared state schema passed between all agent nodes in the LangGraph workflow.
"""

import operator
from typing import Annotated, Any, Optional, TypedDict


class SourceCitation(TypedDict):
    """A single source citation used in the final report."""

    source: str
    snippet: str
    origin: str  # "rag" | "web"


class AgentState(TypedDict, total=False):
    """
    The shared, mutable state object passed between all LangGraph nodes.

    Fields are optional (total=False) since each agent populates only
    the fields relevant to its stage of the pipeline.
    """

    # ---- Input ----
    session_id: str
    original_query: str

    # ---- Supervisor ----
    route_decision: str  # "rag_and_web" | "rag_only" | "web_only" | "direct"
    use_rag: bool
    use_web: bool

    # ---- Query Rewriter ----
    rewritten_query: str
    conversation_context: str

    # ---- Retriever ----
    retrieved_chunks: list[dict[str, Any]]
    rag_context: str

    # ---- Web Research ----
    web_results: list[dict[str, Any]]
    web_context: str

    # ---- Verification ----
    verification_notes: str
    is_sufficient: bool

    # ---- Hallucination Checker ----
    hallucination_score: float
    confidence_score: float
    hallucination_flags: list[str]

    # ---- Report Generator ----
    final_answer: str
    report_markdown: str
    report_file_path: str
    citations: list[SourceCitation]

    # ---- Memory ----
    memory_updated: bool

    # ---- Control / Error handling ----
    errors: Annotated[list[str], operator.add]
    iteration_count: int
