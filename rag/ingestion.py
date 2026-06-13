"""
rag/ingestion.py
End-to-end ingestion pipeline: PDF -> text -> chunks -> vector store + SQLite record.
"""

from pathlib import Path
from typing import Optional

from database.models import add_document_record, delete_document_record
from logger import get_logger
from rag.vector_store import get_vector_store
from utils.pdf_loader import extract_text_from_pdf
from utils.text_splitter import split_text

logger = get_logger(__name__)


def ingest_pdf(file_path: str, session_id: Optional[str] = None) -> dict:
    """
    Ingest a PDF file into the RAG vector store.

    Steps:
        1. Extract raw text from the PDF.
        2. Split text into overlapping chunks.
        3. Embed and store chunks in ChromaDB with source metadata.
        4. Record document metadata in SQLite.

    Args:
        file_path: Path to the PDF file on disk.
        session_id: Optional session ID to associate with this document.

    Returns:
        A dict summary: {"filename": str, "chunks": int, "status": "success"}.
    """
    path = Path(file_path)
    filename = path.name

    try:
        raw_text = extract_text_from_pdf(path)
        chunks = split_text(raw_text)

        metadatas = [
            {"source": filename, "chunk_index": i, "source_type": "pdf"}
            for i in range(len(chunks))
        ]

        vector_store = get_vector_store()
        vector_store.add_documents(texts=chunks, metadatas=metadatas)

        add_document_record(filename=filename, chunk_count=len(chunks), session_id=session_id)

        logger.info("Successfully ingested PDF '%s' with %d chunks.", filename, len(chunks))
        return {"filename": filename, "chunks": len(chunks), "status": "success"}

    except Exception as exc:
        logger.exception("Failed to ingest PDF '%s'.", filename)
        return {"filename": filename, "chunks": 0, "status": "error", "error": str(exc)}


def delete_document(filename: str, doc_id: Optional[int] = None) -> dict:
    """
    Remove a document's chunks from the vector store and its DB record.

    Args:
        filename: The filename used as the 'source' metadata key.
        doc_id: Optional database record ID to delete alongside the vectors.

    Returns:
        A dict summary: {"filename": str, "chunks_deleted": int, "status": "success"}.
    """
    try:
        vector_store = get_vector_store()
        chunks_deleted = vector_store.delete_by_source(filename)

        if doc_id is not None:
            delete_document_record(doc_id)

        logger.info("Deleted document '%s' (%d chunks).", filename, chunks_deleted)
        return {"filename": filename, "chunks_deleted": chunks_deleted, "status": "success"}

    except Exception as exc:
        logger.exception("Failed to delete document '%s'.", filename)
        return {"filename": filename, "chunks_deleted": 0, "status": "error", "error": str(exc)}
