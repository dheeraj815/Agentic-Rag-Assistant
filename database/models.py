"""
database/models.py
Repository-style data access functions for sessions, messages, documents, and reports.
Uses Pydantic models for type-safe representation of database rows.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from database.db import get_connection, init_db
from logger import get_logger

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ===================== Pydantic Models =====================


class Session(BaseModel):
    session_id: str
    created_at: str
    title: Optional[str] = None


class Message(BaseModel):
    id: Optional[int] = None
    session_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    created_at: str = Field(default_factory=_now)
    metadata: Optional[dict] = None


class DocumentRecord(BaseModel):
    id: Optional[int] = None
    filename: str
    chunk_count: int
    uploaded_at: str = Field(default_factory=_now)
    session_id: Optional[str] = None


class ReportRecord(BaseModel):
    id: Optional[int] = None
    session_id: str
    query: str
    file_path: str
    confidence_score: Optional[float] = None
    hallucination_score: Optional[float] = None
    created_at: str = Field(default_factory=_now)


# ===================== Session Operations =====================


def create_session(session_id: str, title: Optional[str] = None) -> None:
    """Create a new chat session if it doesn't already exist."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sessions (session_id, created_at, title) "
                "VALUES (?, ?, ?)",
                (session_id, _now(), title),
            )
        logger.info("Session created/ensured: %s", session_id)
    except Exception:
        logger.exception("Failed to create session %s", session_id)
        raise


def list_sessions() -> list[Session]:
    """Return all sessions ordered by most recent first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC"
        ).fetchall()
    return [Session(**dict(r)) for r in rows]


# ===================== Message Operations =====================


def add_message(
    session_id: str, role: str, content: str, metadata: Optional[dict[str, Any]] = None
) -> None:
    """Persist a chat message to the database."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, created_at, metadata) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    session_id,
                    role,
                    content,
                    _now(),
                    json.dumps(metadata) if metadata else None,
                ),
            )
        logger.debug("Message added for session %s (role=%s)", session_id, role)
    except Exception:
        logger.exception("Failed to add message for session %s", session_id)
        raise


def get_messages(session_id: str, limit: int = 50) -> list[Message]:
    """Retrieve the most recent N messages for a session, oldest first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()

    messages = []
    for r in reversed(rows):
        row_dict = dict(r)
        meta = row_dict.get("metadata")
        row_dict["metadata"] = json.loads(meta) if meta else None
        messages.append(Message(**row_dict))
    return messages


# ===================== Document Operations =====================


def add_document_record(
    filename: str, chunk_count: int, session_id: Optional[str] = None
) -> None:
    """Record metadata for an uploaded/ingested PDF document."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO documents (filename, chunk_count, uploaded_at, session_id) "
                "VALUES (?, ?, ?, ?)",
                (filename, chunk_count, _now(), session_id),
            )
        logger.info("Document record added: %s (%d chunks)", filename, chunk_count)
    except Exception:
        logger.exception("Failed to add document record for %s", filename)
        raise


def list_documents(session_id: Optional[str] = None) -> list[DocumentRecord]:
    """List ingested documents, optionally filtered by session."""
    with get_connection() as conn:
        if session_id:
            rows = conn.execute(
                "SELECT * FROM documents WHERE session_id = ? ORDER BY uploaded_at DESC",
                (session_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY uploaded_at DESC"
            ).fetchall()
    return [DocumentRecord(**dict(r)) for r in rows]


# ===================== Report Operations =====================


def add_report_record(report: ReportRecord) -> int:
    """Persist a generated research report's metadata and return its row id."""
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO reports "
                "(session_id, query, file_path, confidence_score, hallucination_score, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    report.session_id,
                    report.query,
                    report.file_path,
                    report.confidence_score,
                    report.hallucination_score,
                    report.created_at,
                ),
            )
            row_id = cursor.lastrowid
        logger.info("Report record added with id=%s for session=%s", row_id, report.session_id)
        return int(row_id)
    except Exception:
        logger.exception("Failed to add report record for session %s", report.session_id)
        raise


def list_reports(session_id: Optional[str] = None) -> list[ReportRecord]:
    """List generated reports, optionally filtered by session."""
    with get_connection() as conn:
        if session_id:
            rows = conn.execute(
                "SELECT * FROM reports WHERE session_id = ? ORDER BY created_at DESC",
                (session_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM reports ORDER BY created_at DESC"
            ).fetchall()
    return [ReportRecord(**dict(r)) for r in rows]


# Ensure DB schema exists on import
init_db()


# ===================== Document Management =====================


def delete_document_record(doc_id: int) -> bool:
    """Delete a document's metadata record by its ID."""
    try:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Document record %d deleted.", doc_id)
        return deleted
    except Exception:
        logger.exception("Failed to delete document record %d", doc_id)
        return False


def get_document_filenames(session_id: Optional[str] = None) -> list[str]:
    """Return a list of distinct filenames for ingested documents."""
    docs = list_documents(session_id=session_id)
    return [d.filename for d in docs]


# ===================== Session Management =====================


def delete_session(session_id: str) -> bool:
    """Delete a session and all its associated messages and reports."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM reports WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM documents WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        logger.info("Session %s and all associated data deleted.", session_id)
        return True
    except Exception:
        logger.exception("Failed to delete session %s", session_id)
        return False


def update_session_title(session_id: str, title: str) -> bool:
    """Update the display title of a session."""
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET title = ? WHERE session_id = ?", (title, session_id)
            )
        return True
    except Exception:
        logger.exception("Failed to update title for session %s", session_id)
        return False


# ===================== Analytics =====================


class AnalyticsSummary(BaseModel):
    """Aggregate statistics across all sessions for the analytics dashboard."""

    total_sessions: int
    total_messages: int
    total_queries: int
    total_documents: int
    total_chunks: int
    total_reports: int
    avg_confidence: Optional[float] = None
    avg_hallucination: Optional[float] = None


def get_analytics_summary() -> AnalyticsSummary:
    """Compute aggregate analytics across the entire database."""
    try:
        with get_connection() as conn:
            total_sessions = conn.execute("SELECT COUNT(*) AS c FROM sessions").fetchone()["c"]
            total_messages = conn.execute("SELECT COUNT(*) AS c FROM messages").fetchone()["c"]
            total_queries = conn.execute(
                "SELECT COUNT(*) AS c FROM messages WHERE role = 'user'"
            ).fetchone()["c"]
            total_documents = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()["c"]
            total_chunks_row = conn.execute(
                "SELECT COALESCE(SUM(chunk_count), 0) AS c FROM documents"
            ).fetchone()
            total_chunks = total_chunks_row["c"]
            total_reports = conn.execute("SELECT COUNT(*) AS c FROM reports").fetchone()["c"]

            avg_row = conn.execute(
                "SELECT AVG(confidence_score) AS avg_conf, "
                "AVG(hallucination_score) AS avg_halluc FROM reports"
            ).fetchone()
            avg_confidence = avg_row["avg_conf"]
            avg_hallucination = avg_row["avg_halluc"]

        return AnalyticsSummary(
            total_sessions=total_sessions,
            total_messages=total_messages,
            total_queries=total_queries,
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_reports=total_reports,
            avg_confidence=avg_confidence,
            avg_hallucination=avg_hallucination,
        )
    except Exception:
        logger.exception("Failed to compute analytics summary.")
        return AnalyticsSummary(
            total_sessions=0,
            total_messages=0,
            total_queries=0,
            total_documents=0,
            total_chunks=0,
            total_reports=0,
        )


def get_reports_timeseries(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent reports with timestamps and scores, for charting."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT created_at, confidence_score, hallucination_score, query "
                "FROM reports ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]
    except Exception:
        logger.exception("Failed to fetch reports timeseries.")
        return []
