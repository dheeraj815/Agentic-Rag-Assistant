"""
pages/1_Documents.py
Document management page: view, ingest, and remove documents from the
RAG knowledge base.
"""

import tempfile
from pathlib import Path

import streamlit as st

from database.models import list_documents
from rag.ingestion import delete_document, ingest_pdf
from ui.styles import inject_custom_css, render_empty_state, render_footer, render_header

st.set_page_config(page_title="Documents · Agentic RAG", page_icon="📚", layout="wide")
inject_custom_css(st)
render_header(st)

st.markdown("## 📚 Document Management")
st.caption("Manage the knowledge base used by the Retriever Agent for grounded answers.")

st.markdown("---")

# ===================== Bulk Upload =====================

st.markdown("### ⬆️ Upload New Documents")
uploaded_files = st.file_uploader(
    "Upload one or more PDFs",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    if st.button("Ingest All", type="primary"):
        progress = st.progress(0.0)
        status = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            status.text(f"Processing '{uploaded_file.name}'...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            result = ingest_pdf(tmp_path)
            Path(tmp_path).unlink(missing_ok=True)

            if result["status"] == "success":
                st.success(f"✅ {result['filename']} — {result['chunks']} chunks indexed")
            else:
                st.error(f"❌ {result['filename']} — {result.get('error')}")

            progress.progress((i + 1) / len(uploaded_files))

        status.empty()
        st.rerun()

st.markdown("---")

# ===================== Document List =====================

st.markdown("### 📂 Indexed Documents")

docs = list_documents()

if not docs:
    render_empty_state(
        st,
        icon="📭",
        title="No documents indexed",
        subtitle="Upload PDFs above to build your retrieval knowledge base.",
    )
else:
    total_chunks = sum(d.chunk_count for d in docs)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Documents", len(docs))
    with col2:
        st.metric("Total Chunks", total_chunks)

    st.markdown("")

    for d in docs:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.markdown(f"**📄 {d.filename}**")
            with col2:
                st.caption(f"Chunks: {d.chunk_count}")
            with col3:
                st.caption(f"Uploaded: {d.uploaded_at[:10]}")
            with col4:
                if st.button("🗑️", key=f"delete_{d.id}", help="Remove from knowledge base"):
                    result = delete_document(d.filename, doc_id=d.id)
                    if result["status"] == "success":
                        st.success(f"Removed {d.filename} ({result['chunks_deleted']} chunks)")
                        st.rerun()
                    else:
                        st.error(f"Failed to remove: {result.get('error')}")

render_footer(st)
