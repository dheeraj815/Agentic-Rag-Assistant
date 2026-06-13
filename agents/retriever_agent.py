"""
agents/retriever_agent.py
Retriever Agent: fetches relevant chunks from the ChromaDB vector store
for the rewritten query and formats them into context text.
"""

from graph.state import AgentState
from logger import get_logger
from rag.retriever import retrieve_relevant_chunks

logger = get_logger(__name__)


def retriever_node(state: AgentState) -> AgentState:
    """
    Retriever node: populates `retrieved_chunks` and `rag_context`.

    If `use_rag` is False, this node is a no-op passthrough.
    """
    if not state.get("use_rag", False):
        logger.info("Retriever node skipped (use_rag=False).")
        return {"retrieved_chunks": [], "rag_context": ""}

    query = state.get("rewritten_query") or state.get("original_query", "")

    try:
        chunks = retrieve_relevant_chunks(query)

        if not chunks:
            logger.info("Retriever found no relevant chunks for query: '%s'", query)
            return {"retrieved_chunks": [], "rag_context": ""}

        formatted_parts = []
        chunk_dicts = []
        for i, c in enumerate(chunks, start=1):
            formatted_parts.append(
                f"[Document Source {i}: {c.source}]\n{c.text}"
            )
            chunk_dicts.append(c.model_dump())

        rag_context = "\n\n---\n\n".join(formatted_parts)

        logger.info("Retriever node found %d relevant chunks.", len(chunks))

        return {
            "retrieved_chunks": chunk_dicts,
            "rag_context": rag_context,
        }

    except Exception as exc:
        logger.exception("Retriever agent failed.")
        return {"retrieved_chunks": [], "rag_context": "", "errors": [f"RetrieverAgent error: {exc}"]}
