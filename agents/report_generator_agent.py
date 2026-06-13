"""
agents/report_generator_agent.py
Report Generator Agent: assembles a structured Markdown research report
with citations, confidence/hallucination scores, and saves it to disk.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from graph.state import AgentState, SourceCitation
from logger import get_logger

logger = get_logger(__name__)


def _slugify(text: str, max_len: int = 40) -> str:
    """Convert text into a filesystem-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    slug = re.sub(r"[\s-]+", "_", slug)
    return slug[:max_len] or "report"


def _build_citations(state: AgentState) -> list[SourceCitation]:
    """Build a unified list of citations from RAG chunks and web results."""
    citations: list[SourceCitation] = []

    for chunk in state.get("retrieved_chunks", []):
        text = chunk.get("text", "")
        citations.append(
            SourceCitation(
                source=chunk.get("source", "unknown"),
                snippet=(text[:200] + "...") if len(text) > 200 else text,
                origin="rag",
            )
        )

    for r in state.get("web_results", []):
        content = r.get("content", "")
        citations.append(
            SourceCitation(
                source=f"{r.get('title', 'Untitled')} ({r.get('url', '')})",
                snippet=(content[:200] + "...") if len(content) > 200 else content,
                origin="web",
            )
        )

    return citations


def _build_markdown_report(state: AgentState, citations: list[SourceCitation]) -> str:
    """Build the full Markdown research report."""
    query = state.get("original_query", "")
    rewritten = state.get("rewritten_query", query)
    final_answer = state.get("final_answer", "")
    confidence = state.get("confidence_score", 0.0)
    hallucination = state.get("hallucination_score", 0.0)
    flags = state.get("hallucination_flags", [])
    notes = state.get("verification_notes", "")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines.append(f"# Research Report")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append("")
    lines.append(f"## Original Query")
    lines.append(query)
    lines.append("")

    if rewritten and rewritten != query:
        lines.append(f"## Rewritten Query")
        lines.append(rewritten)
        lines.append("")

    lines.append(f"## Answer")
    lines.append(final_answer)
    lines.append("")

    lines.append(f"## Quality Metrics")
    lines.append(f"- **Confidence Score:** {confidence:.2f} / 1.00")
    lines.append(f"- **Hallucination Risk Score:** {hallucination:.2f} / 1.00 "
                  f"(lower is better)")
    if notes:
        lines.append(f"- **Verification Notes:** {notes}")
    lines.append("")

    if flags:
        lines.append(f"## Potential Issues Flagged")
        for f in flags:
            lines.append(f"- {f}")
        lines.append("")

    if citations:
        lines.append(f"## Sources & Citations")
        for i, c in enumerate(citations, start=1):
            origin_label = "Document" if c["origin"] == "rag" else "Web"
            lines.append(f"{i}. **[{origin_label}]** {c['source']}")
            lines.append(f"   > {c['snippet']}")
        lines.append("")

    errors = state.get("errors", [])
    if errors:
        lines.append(f"## Pipeline Warnings")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    return "\n".join(lines)


def report_generator_node(state: AgentState) -> AgentState:
    """
    Report Generator node: populates `report_markdown`, `report_file_path`,
    and `citations`.
    """
    try:
        citations = _build_citations(state)
        report_markdown = _build_markdown_report(state, citations)

        reports_dir = settings.base_dir / Path(settings.REPORTS_DIR)
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        query_slug = _slugify(state.get("original_query", "query"))
        filename = f"report_{timestamp}_{query_slug}.md"
        file_path = reports_dir / filename

        file_path.write_text(report_markdown, encoding="utf-8")

        logger.info("Report generated and saved to: %s", file_path)

        return {
            **state,
            "report_markdown": report_markdown,
            "report_file_path": str(file_path),
            "citations": citations,
        }

    except Exception as exc:
        logger.exception("Report generator agent failed.")
        return {
            **state,
            "report_markdown": state.get("final_answer", ""),
            "report_file_path": "",
            "citations": [],
            "errors": [f"ReportGeneratorAgent error: {exc}"],
        }
