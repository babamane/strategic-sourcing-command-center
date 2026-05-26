# tools/search_tool.py

from typing import Optional, Literal, List, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from duckduckgo_search import DDGS  # Correct import for duckduckgo-search package
import requests
from bs4 import BeautifulSoup
import json


# ---------- 1) INPUT SCHEMA ----------

class DDGSearchArgs(BaseModel):
    """
    Input for AdvancedDuckDuckGoSearchTool.

    Minimal usage:
        {"query": "microsoft q1 fy2026 earnings"}

    Optional:
        mode       : "web" or "news" (default: "news")
        max_results: number of results (default: 3)
        timelimit  : "d", "w", "m", "y" (default: None)
    """
    query: str = Field(..., description="Search query string.")
    mode: Literal["web", "news"] = Field(
        "news",
        description="'web' for general web search, 'news' for news articles.",
    )
    max_results: int = Field(
        3, ge=1, le=10,
        description="Max results to return (1–10).",
    )
    timelimit: Optional[Literal["d", "w", "m", "y"]] = Field(
        None,
        description="Time filter: d=day, w=week, m=month, y=year. None = no filter.",
    )

    # advanced – you normally ignore these
    region: Optional[str] = Field(
        "us-en",
        description="Region like 'us-en', 'in-en'.",
    )
    safesearch: Literal["on", "moderate", "off"] = Field(
        "moderate",
        description="Safe search filter.",
    )
    max_page_chars: int = Field(
        6000,
        description="Max characters per page to keep when fetching article text.",
    )


# ---------- 2) TOOL IMPLEMENTATION ----------

class AdvancedDuckDuckGoSearchTool(BaseTool):
    """
    Advanced DuckDuckGo search tool that:

    - Uses news search by default.
    - Fetches each result URL and extracts the page text.
    - Always returns JSON with `page_text` so you can feed it directly to an LLM.

    Typical use:

        tool = AdvancedDuckDuckGoSearchTool()
        res_json = tool.invoke({"query": "microsoft q1 fy2026 earnings"})
    """

    name: str = "advanced_duckduckgo_search"
    description: str = (
        "Search DuckDuckGo (via ddgs), fetch each result URL, and return "
        "detailed page text in JSON. Designed to be consumed by another LLM step."
    )

    # Pydantic v2 requires annotation
    args_schema: Type[BaseModel] = DDGSearchArgs

    timeout: int = 10
    proxy: Optional[str] = None

    def __init__(self, timeout: int = 10, proxy: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.timeout = timeout
        self.proxy = proxy

    # ----- helpers -----

    def _search_web(
        self,
        query: str,
        max_results: int,
        region: str,
        safesearch: str,
        timelimit: Optional[str],
    ) -> List[Dict[str, Any]]:
        ddgs = DDGS(proxy=self.proxy, timeout=self.timeout)
        return ddgs.text(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=1,
            backend="auto",
        )

    def _search_news(
        self,
        query: str,
        max_results: int,
        region: str,
        safesearch: str,
        timelimit: Optional[str],
    ) -> List[Dict[str, Any]]:
        ddgs = DDGS(proxy=self.proxy, timeout=self.timeout)
        return ddgs.news(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=1,
            backend="auto",
        )

    def _fetch_page_text(self, url: str, max_chars: int) -> Optional[str]:
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except Exception:
            return None

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator=" ")
            text = " ".join(text.split())
            return text[:max_chars]
        except Exception:
            return None

    # ----- sync run -----

    def _run(
        self,
        query: str,
        mode: str = "news",
        max_results: int = 3,
        timelimit: Optional[str] = None,
        region: str = "us-en",
        safesearch: str = "moderate",
        max_page_chars: int = 6000,
    ) -> str:
        """
        Returns JSON string:

        {
          "query": "...",
          "mode": "news",
          "results": [
            {
              "title": "...",
              "url": "...",
              "snippet": "...",
              "published": "...",   # news only
              "page_text": "LONG TEXT..."
            },
            ...
          ]
        }
        """
        try:
            # 1) search
            if mode == "news":
                raw_results = self._search_news(
                    query=query,
                    max_results=max_results,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                )
            else:
                raw_results = self._search_web(
                    query=query,
                    max_results=max_results,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                )
        except Exception as e:
            # return error as JSON instead of exploding the tool
            return json.dumps(
                {
                    "query": query,
                    "mode": mode,
                    "error": f"search_failed: {type(e).__name__}: {e}",
                    "results": [],
                },
                ensure_ascii=False,
            )

        normalized = []
        for r in raw_results:
            if mode == "news":
                title = r.get("title")
                url = r.get("url")
                snippet = r.get("body") or r.get("description") or ""
                published = r.get("date")
                item = {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "published": published,
                }
            else:
                title = r.get("title")
                url = r.get("href")
                snippet = r.get("body") or ""
                item = {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }

            normalized.append(item)

        # 2) fetch detailed page text
        for item in normalized:
            url = item.get("url")
            if not url:
                continue
            page_text = self._fetch_page_text(url, max_page_chars)
            if page_text:
                item["page_text"] = page_text

        # 3) return JSON
        return json.dumps(
            {"query": query, "mode": mode, "results": normalized},
            ensure_ascii=False,
        )

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented for this tool.")

