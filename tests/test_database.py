"""
tests/test_database.py
Tests for SQLite database operations (sessions, messages, documents, reports).
Uses a temporary database file to avoid touching production data.
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Point SQLITE_DB_PATH to a temp file BEFORE importing modules that read settings
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["SQLITE_DB_PATH"] = _tmp_db.name

from database.db import init_db  # noqa: E402
from database.models import (  # noqa: E402
    ReportRecord,
    add_document_record,
    add_message,
    add_report_record,
    create_session,
    get_messages,
    list_documents,
    list_reports,
    list_sessions,
)


def setup_module(_module):
    init_db()


def test_session_and_messages():
    session_id = "test-session-1"
    create_session(session_id, title="Test Session")

    sessions = list_sessions()
    assert any(s.session_id == session_id for s in sessions)

    add_message(session_id, "user", "Hello")
    add_message(session_id, "assistant", "Hi there!", metadata={"score": 0.9})

    messages = get_messages(session_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].metadata == {"score": 0.9}


def test_documents():
    add_document_record("sample.pdf", chunk_count=10, session_id="test-session-1")
    docs = list_documents(session_id="test-session-1")
    assert len(docs) == 1
    assert docs[0].filename == "sample.pdf"
    assert docs[0].chunk_count == 10


def test_reports():
    report = ReportRecord(
        session_id="test-session-1",
        query="What is AI?",
        file_path="/tmp/report_test.md",
        confidence_score=0.85,
        hallucination_score=0.1,
    )
    report_id = add_report_record(report)
    assert report_id > 0

    reports = list_reports(session_id="test-session-1")
    assert len(reports) == 1
    assert reports[0].query == "What is AI?"


def teardown_module(_module):
    try:
        os.unlink(_tmp_db.name)
    except OSError:
        pass


if __name__ == "__main__":
    setup_module(None)
    test_session_and_messages()
    test_documents()
    test_reports()
    teardown_module(None)
    print("All database tests passed.")
