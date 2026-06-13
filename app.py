"""
app.py
Agentic RAG Research Assistant — Professional Streamlit Dashboard (Chat page).

Run with:
    streamlit run app.py
"""

import tempfile
import uuid
from pathlib import Path

import streamlit as st

from database.models import (
    create_session,
    get_messages,
    list_documents,
)
from graph.workflow import get_workflow
from logger import get_logger
from rag.ingestion import ingest_pdf
from ui.export import export_chat_as_json, export_chat_as_markdown, export_chat_as_text
from ui.styles import (
    inject_custom_css,
    render_empty_state,
    render_footer,
    render_header,
    render_pipeline_track,
    render_source_card,
)
from utils.verification_claude import claude_verify

logger = get_logger(__name__)

st.set_page_config(
    page_title="Agentic RAG Research Assistant",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css(st)


# ===================== Session State Initialization =====================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    create_session(st.session_state.session_id, title="New Research Session")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "enable_claude_verification" not in st.session_state:
    st.session_state.enable_claude_verification = False


# ===================== Sidebar =====================

with st.sidebar:
    st.markdown("### 🔎 Agentic RAG Assistant")
    st.caption("Multi-Agent Research System · LangGraph + Groq")

    st.markdown("---")
    st.markdown("### 📄 Document Upload")

    uploaded_file = st.file_uploader(
        "Upload a PDF", type=["pdf"], label_visibility="collapsed"
    )
    if uploaded_file is not None:
        if st.button("⬆️ Ingest PDF", use_container_width=True, type="primary"):
            with st.spinner(f"Processing '{uploaded_file.name}'..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name

                result = ingest_pdf(tmp_path, session_id=st.session_state.session_id)
                Path(tmp_path).unlink(missing_ok=True)

                if result["status"] == "success":
                    st.success(
                        f"✅ Ingested **{result['filename']}** "
                        f"({result['chunks']} chunks indexed)"
                    )
                else:
                    st.error(f"❌ Failed: {result.get('error')}")

    st.markdown("---")
    st.markdown("### 📚 Indexed Documents")
    docs = list_documents()
    if docs:
        total_chunks = sum(d.chunk_count for d in docs)
        st.caption(f"{len(docs)} document(s) · {total_chunks} chunks total")
        for d in docs[:8]:
            st.text(f"• {d.filename}")
        if len(docs) > 8:
            st.caption(f"...and {len(docs) - 8} more (see Documents page)")
    else:
        st.caption("No documents indexed yet.")

    st.markdown("---")
    st.markdown("### ⚙️ Settings")

    st.session_state.enable_claude_verification = st.checkbox(
        "Enable Claude verification (optional)",
        value=st.session_state.enable_claude_verification,
        help="Requires ANTHROPIC_API_KEY in .env. Runs a secondary independent check.",
    )

    st.markdown("---")
    st.markdown("### 💾 Export Chat")

    if st.session_state.chat_history:
        messages = get_messages(st.session_state.session_id, limit=200)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                "MD",
                data=export_chat_as_markdown(messages, st.session_state.session_id),
                file_name="conversation.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "JSON",
                data=export_chat_as_json(messages, st.session_state.session_id),
                file_name="conversation.json",
                mime="application/json",
                use_container_width=True,
            )
        with col3:
            st.download_button(
                "TXT",
                data=export_chat_as_text(messages, st.session_state.session_id),
                file_name="conversation.txt",
                mime="text/plain",
                use_container_width=True,
            )
    else:
        st.caption("No conversation to export yet.")

    st.markdown("---")
    if st.button("🗑️ New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        create_session(st.session_state.session_id, title="New Research Session")
        st.session_state.chat_history = []
        st.rerun()

    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")


# ===================== Main Area =====================

render_header(st)

# Render chat history
if not st.session_state.chat_history:
    render_empty_state(
        st,
        icon="🧠",
        title="Start your research",
        subtitle="Ask a question below. The multi-agent pipeline will research, verify, "
        "and cite sources for you.",
    )
else:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            meta = msg.get("meta")
            if meta:
                with st.expander("📊 Details & Sources"):
                    confidence = meta.get("confidence_score", 0.0)
                    hallucination = meta.get("hallucination_score", 0.0)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Confidence Score", f"{confidence:.2f}")
                    with col2:
                        st.metric("Hallucination Risk", f"{hallucination:.2f}")

                    if meta.get("verification_notes"):
                        st.markdown(f"**🔍 Verification:** {meta['verification_notes']}")

                    if meta.get("hallucination_flags"):
                        st.markdown("**⚠️ Flags:**")
                        for f in meta["hallucination_flags"]:
                            st.markdown(f"- {f}")

                    if meta.get("citations"):
                        st.markdown("**📎 Sources:**")
                        for c in meta["citations"]:
                            st.markdown(
                                render_source_card(c["source"], c["snippet"], c["origin"]),
                                unsafe_allow_html=True,
                            )

                    if meta.get("claude_review"):
                        st.markdown(f"**🤖 Claude Review:** {meta['claude_review']}")

                    if meta.get("report_file_path"):
                        report_path = Path(meta["report_file_path"])
                        if report_path.exists():
                            with open(report_path, "rb") as f:
                                st.download_button(
                                    "📥 Download Full Report (.md)",
                                    data=f.read(),
                                    file_name=report_path.name,
                                    mime="text/markdown",
                                    key=f"download_{report_path.name}_{msg['content'][:10]}",
                                )

                    if meta.get("errors"):
                        st.markdown("**⚠️ Pipeline Warnings:**")
                        for e in meta["errors"]:
                            st.warning(e)


# Chat input
user_query = st.chat_input("Ask a research question...")

if user_query:
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        pipeline_placeholder = st.empty()
        answer_placeholder = st.empty()

        completed_steps: list[str] = []
        final_state: dict = {}

        try:
            workflow = get_workflow()
            initial_state = {
                "session_id": st.session_state.session_id,
                "original_query": user_query,
                "errors": [],
            }

            # Stream node-by-node so the UI shows live pipeline progress
            for step_output in workflow.stream(initial_state, stream_mode="updates"):
                for node_name, node_state in step_output.items():
                    with pipeline_placeholder.container():
                        render_pipeline_track(
                            st, active_step=node_name, completed_steps=completed_steps
                        )
                    completed_steps.append(node_name)
                    if isinstance(node_state, dict):
                        final_state.update(node_state)

            with pipeline_placeholder.container():
                render_pipeline_track(st, active_step="", completed_steps=completed_steps)

            final_answer = final_state.get("final_answer", "No answer generated.")
            claude_review = None

            if st.session_state.enable_claude_verification:
                combined_context = "\n\n".join(
                    filter(
                        None,
                        [
                            final_state.get("rag_context", ""),
                            final_state.get("web_context", ""),
                        ],
                    )
                )
                if combined_context.strip():
                    with st.spinner("Running optional Claude verification..."):
                        claude_review = claude_verify(combined_context, final_answer)

            answer_placeholder.markdown(final_answer)

            meta = {
                "confidence_score": final_state.get("confidence_score", 0.0),
                "hallucination_score": final_state.get("hallucination_score", 0.0),
                "verification_notes": final_state.get("verification_notes", ""),
                "hallucination_flags": final_state.get("hallucination_flags", []),
                "citations": final_state.get("citations", []),
                "report_file_path": final_state.get("report_file_path", ""),
                "errors": final_state.get("errors", []),
                "claude_review": claude_review,
            }

            st.session_state.chat_history.append(
                {"role": "assistant", "content": final_answer, "meta": meta}
            )
            st.rerun()

        except Exception as exc:
            logger.exception("Pipeline execution failed.")
            error_msg = f"An error occurred while processing your request: {exc}"
            pipeline_placeholder.empty()
            answer_placeholder.error(error_msg)
            st.session_state.chat_history.append(
                {"role": "assistant", "content": error_msg, "meta": {}}
            )


render_footer(st)
