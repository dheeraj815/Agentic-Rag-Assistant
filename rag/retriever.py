"""
rag/retriever.py
Retrieval interface over the vector store, returning structured results
with source citations.
"""

from typing import Optional

from pydantic import BaseModel

from config import settings
from logger import get_logger
from rag.vector_store import get_vector_store

logger = get_logger(__name__)


class RetrievedChunk(BaseModel):
    """A single retrieved chunk with its source metadata and relevance score."""

    text: str
    source: str
    chunk_index: Optional[int] = None
    score: float


def retrieve_relevant_chunks(query: str, k: Optional[int] = None) -> list[RetrievedChunk]:
    """
    Retrieve the top-k most relevant chunks from the vector store for a query.

    Args:
        query: The (possibly rewritten) search query.
        k: Number of chunks to retrieve (defaults to settings.TOP_K_RESULTS).

    Returns:
        A list of RetrievedChunk objects, sorted by relevance (lower score = closer).
    """
    k = k or settings.TOP_K_RESULTS

    try:
        vector_store = get_vector_store()
        raw_results = vector_store.similarity_search(query=query, k=k)

        chunks = []
        for r in raw_results:
            metadata = r.get("metadata", {})
            chunks.append(
                RetrievedChunk(
                    text=r["text"],
                    source=metadata.get("source", "unknown"),
                    chunk_index=metadata.get("chunk_index"),
                    score=r.get("score", 0.0),
                )
            )

        logger.info("Retrieved %d chunks for query: '%s'", len(chunks), query)
        return chunks

    except Exception:
        logger.exception("Retrieval failed for query: '%s'", query)
        return []


def has_indexed_documents() -> bool:
    """Return True if the vector store contains any indexed chunks."""
    try:
        return get_vector_store().count() > 0
    except Exception:
        logger.exception("Failed to check vector store document count.")
        return False
