"""
rag/vector_store.py
ChromaDB-backed vector store using Sentence Transformers embeddings.
"""

import uuid
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.utils import embedding_functions

from config import settings
from logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    Thin wrapper around a persistent ChromaDB collection using a
    Sentence Transformers embedding function.
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ) -> None:
        self.persist_dir = str(
            settings.base_dir / Path(persist_dir or settings.CHROMA_PERSIST_DIR)
        )
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.embedding_model_name = embedding_model or settings.EMBEDDING_MODEL

        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        try:
            self._client = chromadb.PersistentClient(path=self.persist_dir)
            self._embedding_fn = (
                embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.embedding_model_name
                )
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "VectorStore initialized (collection=%s, persist_dir=%s, model=%s)",
                self.collection_name,
                self.persist_dir,
                self.embedding_model_name,
            )
        except Exception:
            logger.exception("Failed to initialize ChromaDB vector store.")
            raise

    def add_documents(
        self,
        texts: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
        ids: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Add a list of text chunks to the vector store.

        Args:
            texts: List of text chunks to embed and store.
            metadatas: Optional list of metadata dicts (one per chunk).
            ids: Optional list of unique IDs (auto-generated if not provided).

        Returns:
            The list of IDs used for the inserted documents.
        """
        if not texts:
            return []

        ids = ids or [str(uuid.uuid4()) for _ in texts]
        metadatas = metadatas or [{} for _ in texts]

        try:
            self._collection.add(documents=texts, metadatas=metadatas, ids=ids)
            logger.info("Added %d documents to vector store.", len(texts))
            return ids
        except Exception:
            logger.exception("Failed to add documents to vector store.")
            raise

    def similarity_search(
        self, query: str, k: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """
        Perform a similarity search against the vector store.

        Args:
            query: The natural-language query string.
            k: Number of results to return (defaults to settings.TOP_K_RESULTS).

        Returns:
            A list of dicts each containing 'text', 'metadata', and 'score' (distance).
        """
        k = k or settings.TOP_K_RESULTS

        try:
            count = self._collection.count()
            if count == 0:
                logger.info("Vector store is empty; returning no results.")
                return []

            k = min(k, count)
            results = self._collection.query(query_texts=[query], n_results=k)

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            output = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                output.append({"text": doc, "metadata": meta or {}, "score": dist})

            logger.info("Similarity search returned %d results for query.", len(output))
            return output
        except Exception:
            logger.exception("Similarity search failed.")
            raise

    def count(self) -> int:
        """Return the number of items currently stored in the collection."""
        try:
            return self._collection.count()
        except Exception:
            logger.exception("Failed to count vector store items.")
            return 0

    def delete_by_source(self, source: str) -> int:
        """
        Delete all chunks belonging to a given source filename.

        Args:
            source: The source filename (matches metadata['source']).

        Returns:
            The number of chunks deleted.
        """
        try:
            results = self._collection.get(where={"source": source})
            ids = results.get("ids", [])
            if ids:
                self._collection.delete(ids=ids)
                logger.info("Deleted %d chunks for source '%s'.", len(ids), source)
            return len(ids)
        except Exception:
            logger.exception("Failed to delete chunks for source '%s'.", source)
            return 0

    def reset(self) -> None:
        """Delete and recreate the collection (clears all stored vectors)."""
        try:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Vector store collection '%s' reset.", self.collection_name)
        except Exception:
            logger.exception("Failed to reset vector store collection.")
            raise


_vector_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Return a singleton VectorStore instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
