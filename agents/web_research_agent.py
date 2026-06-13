"""
agents/web_research_agent.py
Web Research Agent: performs live web search via Tavily and formats
results into context text with source citations.
"""

from tavily import TavilyClient

from config import settings
from graph.state import AgentState
from logger import get_logger

logger = get_logger(__name__)

MAX_WEB_RESULTS = 5


def web_research_node(state: AgentState) -> AgentState:
    """
    Web Research node: populates `web_results` and `web_context`.

    If `use_web` is False, this node is a no-op passthrough.
    """
    if not state.get("use_web", False):
        logger.info("Web research node skipped (use_web=False).")
        return {"web_results": [], "web_context": ""}

    if not settings.TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not configured; skipping web search.")
        return {"web_results": [], "web_context": "", "errors": ["WebResearchAgent error: TAVILY_API_KEY not configured."]}

    query = state.get("rewritten_query") or state.get("original_query", "")

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(
            query=query,
            max_results=MAX_WEB_RESULTS,
            search_depth="advanced",
            include_answer=False,
        )

        results = response.get("results", [])

        web_results = []
        formatted_parts = []
        for i, r in enumerate(results, start=1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            content = r.get("content", "")

            web_results.append(
                {"title": title, "url": url, "content": content}
            )
            formatted_parts.append(
                f"[Web Source {i}: {title} ({url})]\n{content}"
            )

        web_context = "\n\n---\n\n".join(formatted_parts)

        logger.info("Web research node found %d results for query: '%s'", len(web_results), query)

        return {
            "web_results": web_results,
            "web_context": web_context,
        }

    except Exception as exc:
        logger.exception("Web research agent failed.")
        return {"web_results": [], "web_context": "", "errors": [f"WebResearchAgent error: {exc}"]}
