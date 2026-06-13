"""
ui/export.py
Utilities for exporting chat history and research reports in multiple formats.
"""

import json
from datetime import datetime, timezone
from typing import Any

from database.models import Message


def export_chat_as_markdown(messages: list[Message], session_id: str) -> str:
    """
    Export a conversation as a formatted Markdown transcript.

    Args:
        messages: List of Message objects (oldest first).
        session_id: The session identifier (included in the header).

    Returns:
        A Markdown-formatted string of the full conversation.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Research Assistant Conversation Export",
        "",
        f"**Session ID:** `{session_id}`",
        f"**Exported:** {timestamp}",
        f"**Total Messages:** {len(messages)}",
        "",
        "---",
        "",
    ]

    for m in messages:
        role_label = "🧑 User" if m.role == "user" else "🤖 Assistant"
        lines.append(f"### {role_label}")
        lines.append(f"*{m.created_at}*")
        lines.append("")
        lines.append(m.content)
        lines.append("")

        if m.metadata:
            conf = m.metadata.get("confidence_score")
            halluc = m.metadata.get("hallucination_score")
            if conf is not None or halluc is not None:
                lines.append(
                    f"> Confidence: {conf:.2f} | Hallucination Risk: {halluc:.2f}"
                    if conf is not None and halluc is not None
                    else ""
                )
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def export_chat_as_json(messages: list[Message], session_id: str) -> str:
    """
    Export a conversation as a structured JSON document.

    Args:
        messages: List of Message objects (oldest first).
        session_id: The session identifier.

    Returns:
        A pretty-printed JSON string.
    """
    data: dict[str, Any] = {
        "session_id": session_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "message_count": len(messages),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at,
                "metadata": m.metadata,
            }
            for m in messages
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def export_chat_as_text(messages: list[Message], session_id: str) -> str:
    """
    Export a conversation as a plain-text transcript (no markdown formatting).

    Args:
        messages: List of Message objects (oldest first).
        session_id: The session identifier.

    Returns:
        A plain-text transcript.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "RESEARCH ASSISTANT CONVERSATION EXPORT",
        f"Session ID: {session_id}",
        f"Exported: {timestamp}",
        f"Total Messages: {len(messages)}",
        "=" * 60,
        "",
    ]

    for m in messages:
        role_label = "USER" if m.role == "user" else "ASSISTANT"
        lines.append(f"[{m.created_at}] {role_label}:")
        lines.append(m.content)
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

    return "\n".join(lines)
