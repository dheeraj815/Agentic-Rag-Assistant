"""
utils/text_splitter.py
Text chunking utilities built on LangChain's RecursiveCharacterTextSplitter.
"""

from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings
from logger import get_logger

logger = get_logger(__name__)


def split_text(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[str]:
    """
    Split a long text into overlapping chunks suitable for embedding.

    Args:
        text: The raw text to split.
        chunk_size: Maximum characters per chunk (defaults to settings.CHUNK_SIZE).
        chunk_overlap: Overlap between consecutive chunks
            (defaults to settings.CHUNK_OVERLAP).

    Returns:
        A list of text chunks.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_text(text)
    logger.info(
        "Split text into %d chunks (chunk_size=%d, overlap=%d)",
        len(chunks),
        chunk_size,
        chunk_overlap,
    )
    return chunks
