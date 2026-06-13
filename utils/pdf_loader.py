"""
utils/pdf_loader.py
Utilities for extracting text content from uploaded PDF files.
"""

from pathlib import Path
from typing import Union

from pypdf import PdfReader

from logger import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(file_path: Union[str, Path]) -> str:
    """
    Extract all text content from a PDF file.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        Concatenated text content of all pages, separated by double newlines.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If no text could be extracted (e.g. scanned/image-only PDF).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        reader = PdfReader(str(path))
        pages_text = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception:
                logger.warning("Failed to extract text from page %d of %s", i, path.name)
                text = ""
            if text.strip():
                pages_text.append(text)

        full_text = "\n\n".join(pages_text)
        if not full_text.strip():
            raise ValueError(
                f"No extractable text found in '{path.name}'. "
                "The PDF may be scanned/image-based."
            )

        logger.info(
            "Extracted text from PDF '%s': %d pages, %d characters",
            path.name,
            len(reader.pages),
            len(full_text),
        )
        return full_text

    except Exception:
        logger.exception("Failed to extract text from PDF: %s", path)
        raise
