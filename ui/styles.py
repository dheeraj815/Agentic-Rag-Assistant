"""
ui/styles.py
Custom CSS injection for a polished, professional Streamlit interface.
"""

CUSTOM_CSS = """
<style>
    /* ===== Global ===== */
    .stApp {
        background: linear-gradient(180deg, #0E1117 0%, #0B0E14 100%);
    }

    /* ===== Header / Title ===== */
    .app-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem 0 1rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1.25rem;
    }
    .app-header .logo {
        font-size: 2.2rem;
        line-height: 1;
    }
    .app-header .title-block h1 {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, #818CF8, #C084FC);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .app-header .title-block p {
        margin: 0;
        font-size: 0.85rem;
        color: #9CA3AF;
    }

    /* ===== Pipeline status badges ===== */
    .pipeline-track {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin: 0.5rem 0 1rem 0;
    }
    .pipeline-step {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        background: rgba(99,102,241,0.12);
        color: #A5B4FC;
        border: 1px solid rgba(99,102,241,0.25);
        white-space: nowrap;
    }
    .pipeline-step.done {
        background: rgba(34,197,94,0.12);
        color: #86EFAC;
        border-color: rgba(34,197,94,0.25);
    }
    .pipeline-step.active {
        background: rgba(251,191,36,0.14);
        color: #FCD34D;
        border-color: rgba(251,191,36,0.3);
        animation: pulse 1.4s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* ===== Metric cards ===== */
    .metric-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        text-align: center;
    }
    .metric-card .metric-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9CA3AF;
        margin-bottom: 0.25rem;
    }
    .metric-card .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
    }
    .metric-good { color: #4ADE80; }
    .metric-warn { color: #FBBF24; }
    .metric-bad { color: #F87171; }

    /* ===== Source / Citation cards ===== */
    .source-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-left: 3px solid #6366F1;
        border-radius: 8px;
        padding: 0.6rem 0.85rem;
        margin-bottom: 0.5rem;
    }
    .source-card.web {
        border-left-color: #22D3EE;
    }
    .source-card .source-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #E5E7EB;
        margin-bottom: 0.15rem;
    }
    .source-card .source-snippet {
        font-size: 0.78rem;
        color: #9CA3AF;
        line-height: 1.4;
    }
    .source-badge {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        padding: 0.1rem 0.4rem;
        border-radius: 4px;
        margin-right: 0.4rem;
    }
    .source-badge.rag {
        background: rgba(99,102,241,0.18);
        color: #A5B4FC;
    }
    .source-badge.web {
        background: rgba(34,211,238,0.15);
        color: #67E8F9;
    }

    /* ===== Sidebar polish ===== */
    section[data-testid="stSidebar"] {
        background: #0B0E14;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        font-size: 0.95rem;
        color: #E5E7EB;
        margin-bottom: 0.3rem;
    }

    /* ===== Chat bubbles ===== */
    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.6rem;
    }

    /* ===== Buttons ===== */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99,102,241,0.25);
    }

    /* ===== Empty state ===== */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #6B7280;
    }
    .empty-state .icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .empty-state h3 {
        color: #9CA3AF;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    /* ===== Scrollbar ===== */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.12);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

    /* ===== Footer ===== */
    .app-footer {
        text-align: center;
        font-size: 0.72rem;
        color: #4B5563;
        padding: 1.5rem 0 0.5rem 0;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 2rem;
    }
</style>
"""


def inject_custom_css(st) -> None:
    """Inject the custom CSS block into the current Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header(st) -> None:
    """Render the branded application header."""
    st.markdown(
        """
        <div class="app-header">
            <div class="logo">🔎</div>
            <div class="title-block">
                <h1>Agentic RAG Research Assistant</h1>
                <p>Multi-agent research pipeline · LangGraph + Groq · Real-time citations & verification</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline_track(st, active_step: str = "", completed_steps: list | None = None) -> None:
    """
    Render a visual pipeline progress tracker.

    Args:
        st: streamlit module
        active_step: key of the currently running step
        completed_steps: list of step keys already completed
    """
    completed_steps = completed_steps or []
    steps = [
        ("supervisor", "Supervisor"),
        ("query_rewriter", "Query Rewriter"),
        ("retriever", "Retriever"),
        ("web_research", "Web Research"),
        ("verifier", "Verifier"),
        ("hallucination_checker", "Hallucination Check"),
        ("report_generator", "Report Generator"),
        ("memory_agent", "Memory Update"),
    ]

    html_parts = ['<div class="pipeline-track">']
    for key, label in steps:
        css_class = "pipeline-step"
        if key in completed_steps:
            css_class += " done"
        elif key == active_step:
            css_class += " active"
        html_parts.append(f'<span class="{css_class}">{label}</span>')
    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_metric_card(st, label: str, value: str, level: str = "good") -> str:
    """Return HTML for a metric card (level: good | warn | bad)."""
    css_level = {"good": "metric-good", "warn": "metric-warn", "bad": "metric-bad"}.get(
        level, "metric-good"
    )
    return (
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value {css_level}">{value}</div>'
        f"</div>"
    )


def render_source_card(source: str, snippet: str, origin: str) -> str:
    """Return HTML for a single source/citation card."""
    badge_class = "rag" if origin == "rag" else "web"
    badge_label = "Document" if origin == "rag" else "Web"
    card_class = "source-card" if origin == "rag" else "source-card web"
    return (
        f'<div class="{card_class}">'
        f'<div class="source-title">'
        f'<span class="source-badge {badge_class}">{badge_label}</span>{source}'
        f"</div>"
        f'<div class="source-snippet">{snippet}</div>'
        f"</div>"
    )


def render_empty_state(st, icon: str, title: str, subtitle: str) -> None:
    """Render a friendly empty-state placeholder."""
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="icon">{icon}</div>
            <h3>{title}</h3>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer(st) -> None:
    """Render the application footer."""
    st.markdown(
        """
        <div class="app-footer">
            Agentic RAG Research Assistant · Powered by LangGraph, Groq & ChromaDB
        </div>
        """,
        unsafe_allow_html=True,
    )
