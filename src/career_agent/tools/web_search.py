"""Web search tool — DuckDuckGo-based, no API key required."""

from __future__ import annotations

from career_agent.tools.base import Tool, ToolResult


class WebSearchTool(Tool):
    """Search the web for information related to a query.

    Uses DuckDuckGo — no API key needed.  Results are limited to
    snippet text (no full page fetch).
    """

    name = "web_search"
    description = "Search the web for job/company/industry information"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 5},
            },
        }

    @property
    def safety_notes(self) -> list[str]:
        return [
            "只搜索公开信息，不访问需要登录的页面",
            "搜索结果作为参考，不作为 evidence 直接用于简历",
            "不搜索个人隐私信息",
        ]

    def run(self, query: str = "", max_results: int = 5, **kwargs) -> ToolResult:  # noqa: ARG002
        if not query.strip():
            return ToolResult(success=False, error="query is required", summary="empty query")

        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")[:300],
                    })
            if not results:
                return ToolResult(
                    success=True,
                    output={"results": [], "query": query},
                    summary=f"no results for: {query[:60]}",
                )
            return ToolResult(
                success=True,
                output={"results": results, "query": query},
                summary=f"found {len(results)} results for: {query[:60]}",
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), summary="web search failed")
