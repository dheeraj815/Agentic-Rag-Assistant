"""
memory/conversation_memory.py
Conversation memory manager backed by SQLite, providing chat history
retrieval and persistence for the Memory Agent.
"""

from typing import Optional

from database.models import add_message, create_session, get_messages, Message
from logger import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """Manages persistent conversation history for a given session."""

    def __init__(self, session_id: str, history_limit: int = 20) -> None:
        self.session_id = session_id
        self.history_limit = history_limit
        create_session(session_id)

    def add_user_message(self, content: str) -> None:
        """Persist a user message."""
        add_message(self.session_id, role="user", content=content)

    def add_assistant_message(self, content: str, metadata: Optional[dict] = None) -> None:
        """Persist an assistant message, optionally with metadata (sources, scores)."""
        add_message(self.session_id, role="assistant", content=content, metadata=metadata)

    def get_history(self, limit: Optional[int] = None) -> list[Message]:
        """Return recent conversation history, oldest first."""
        return get_messages(self.session_id, limit=limit or self.history_limit)

    def get_history_as_text(self, limit: Optional[int] = None) -> str:
        """
        Return conversation history formatted as a plain-text transcript,
        suitable for inclusion in LLM prompts.
        """
        messages = self.get_history(limit=limit)
        if not messages:
            return "No prior conversation history."

        lines = []
        for m in messages:
            role_label = "User" if m.role == "user" else "Assistant"
            lines.append(f"{role_label}: {m.content}")
        return "\n".join(lines)

    def get_recent_context_summary(self, limit: int = 6) -> str:
        """
        Return a condensed summary of recent turns (last `limit` messages)
        for use in query rewriting.
        """
        messages = self.get_history(limit=limit)
        if not messages:
            return ""

        lines = []
        for m in messages:
            role_label = "User" if m.role == "user" else "Assistant"
            content = m.content[:300]
            lines.append(f"{role_label}: {content}")
        return "\n".join(lines)
