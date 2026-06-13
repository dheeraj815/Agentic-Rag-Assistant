"""
pages/2_Analytics.py
Analytics dashboard: aggregate statistics across all sessions, including
confidence/hallucination trends over time.
"""

import pandas as pd
import streamlit as st

from database.models import get_analytics_summary, get_reports_timeseries, list_sessions
from ui.styles import inject_custom_css, render_empty_state, render_footer, render_header

st.set_page_config(page_title="Analytics · Agentic RAG", page_icon="📊", layout="wide")
inject_custom_css(st)
render_header(st)

st.markdown("## 📊 Analytics Dashboard")
st.caption("Aggregate insights across all research sessions.")

st.markdown("---")

summary = get_analytics_summary()

# ===================== Top-Level Metrics =====================

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Sessions", summary.total_sessions)
with col2:
    st.metric("Total Queries", summary.total_queries)
with col3:
    st.metric("Documents Indexed", summary.total_documents)
with col4:
    st.metric("Reports Generated", summary.total_reports)

col5, col6, col7 = st.columns(3)
with col5:
    st.metric("Total Chunks", summary.total_chunks)
with col6:
    avg_conf = summary.avg_confidence
    st.metric("Avg. Confidence", f"{avg_conf:.2f}" if avg_conf is not None else "N/A")
with col7:
    avg_halluc = summary.avg_hallucination
    st.metric("Avg. Hallucination Risk", f"{avg_halluc:.2f}" if avg_halluc is not None else "N/A")

st.markdown("---")

# ===================== Quality Trends =====================

st.markdown("### 📈 Quality Score Trends")

timeseries = get_reports_timeseries(limit=50)

if not timeseries:
    render_empty_state(
        st,
        icon="📉",
        title="No report data yet",
        subtitle="Run some research queries to populate quality trend charts.",
    )
else:
    df = pd.DataFrame(timeseries)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values("created_at")
    df_indexed = df.set_index("created_at")[["confidence_score", "hallucination_score"]]
    df_indexed.columns = ["Confidence Score", "Hallucination Risk"]

    st.line_chart(df_indexed, height=320)

    st.markdown("### 🗂️ Recent Reports")
    display_df = df[["created_at", "query", "confidence_score", "hallucination_score"]].copy()
    display_df.columns = ["Timestamp", "Query", "Confidence", "Hallucination Risk"]
    display_df = display_df.sort_values("Timestamp", ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ===================== Sessions Overview =====================

st.markdown("### 🗒️ All Sessions")

sessions = list_sessions()
if not sessions:
    st.caption("No sessions yet.")
else:
    session_df = pd.DataFrame(
        [{"Session ID": s.session_id, "Title": s.title or "Untitled", "Created": s.created_at} for s in sessions]
    )
    st.dataframe(session_df, use_container_width=True, hide_index=True)

render_footer(st)
