"""
pages/4_History.py
Browse, switch between, rename, and delete past research sessions.
"""

import streamlit as st

from database.models import (
    delete_session,
    get_messages,
    list_sessions,
    update_session_title,
)
from ui.export import export_chat_as_json, export_chat_as_markdown, export_chat_as_text
from ui.styles import inject_custom_css, render_empty_state, render_footer, render_header

st.set_page_config(page_title="History · Agentic RAG", page_icon="🕘", layout="wide")
inject_custom_css(st)
render_header(st)

st.markdown("## 🕘 Session History")
st.caption("View, rename, export, or delete past research sessions.")

st.markdown("---")

sessions = list_sessions()

if not sessions:
    render_empty_state(
        st,
        icon="🗂️",
        title="No sessions yet",
        subtitle="Start a conversation on the Chat page to create your first session.",
    )
else:
    current_session_id = st.session_state.get("session_id")

    for s in sessions:
        is_current = s.session_id == current_session_id
        label = f"{'⭐ ' if is_current else ''}{s.title or 'Untitled Session'}"

        with st.expander(f"{label} — {s.created_at[:19]}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                new_title = st.text_input(
                    "Title",
                    value=s.title or "Untitled Session",
                    key=f"title_{s.session_id}",
                )
                if new_title != (s.title or "Untitled Session"):
                    if st.button("Save Title", key=f"save_{s.session_id}"):
                        update_session_title(s.session_id, new_title)
                        st.rerun()

            with col2:
                st.caption(f"ID: `{s.session_id[:12]}...`")
                if is_current:
                    st.success("Active session")

            messages = get_messages(s.session_id, limit=200)
            st.caption(f"{len(messages)} message(s)")

            if messages:
                # Show a brief preview of the conversation
                preview_count = min(2, len(messages))
                for m in messages[:preview_count]:
                    role_label = "🧑" if m.role == "user" else "🤖"
                    preview_text = m.content[:150] + ("..." if len(m.content) > 150 else "")
                    st.markdown(f"{role_label} {preview_text}")

                st.markdown("")
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.download_button(
                        "📥 Export MD",
                        data=export_chat_as_markdown(messages, s.session_id),
                        file_name=f"session_{s.session_id[:8]}.md",
                        mime="text/markdown",
                        key=f"export_md_{s.session_id}",
                        use_container_width=True,
                    )
                with col_b:
                    st.download_button(
                        "📥 Export JSON",
                        data=export_chat_as_json(messages, s.session_id),
                        file_name=f"session_{s.session_id[:8]}.json",
                        mime="application/json",
                        key=f"export_json_{s.session_id}",
                        use_container_width=True,
                    )
                with col_c:
                    st.download_button(
                        "📥 Export TXT",
                        data=export_chat_as_text(messages, s.session_id),
                        file_name=f"session_{s.session_id[:8]}.txt",
                        mime="text/plain",
                        key=f"export_txt_{s.session_id}",
                        use_container_width=True,
                    )
                with col_d:
                    if st.button(
                        "🗑️ Delete Session",
                        key=f"delete_{s.session_id}",
                        use_container_width=True,
                        type="secondary",
                    ):
                        delete_session(s.session_id)
                        if is_current:
                            for key in ["session_id", "chat_history"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                        st.rerun()
            else:
                st.caption("No messages in this session.")
                if st.button("🗑️ Delete Empty Session", key=f"delete_empty_{s.session_id}"):
                    delete_session(s.session_id)
                    st.rerun()

render_footer(st)
