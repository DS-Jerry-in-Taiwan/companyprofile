"""
Tavily 搜尋提供者
==================

使用主流程的 SearchResult dataclass
"""

# 路徑已在 providers/__init__.py 中設定
import os
import sys
import time
import asyncio
from typing import Dict, Any

from src.services.search_tools import SearchResult
from .base_provider import BaseSearchProvider


class TavilySearchProvider(BaseSearchProvider):
    """Tavily 搜尋提供者"""

    @property
    def provider_name(self) -> str:
        return "tavily"

    def __init__(self, max_results: int = 3):
        from src.services.tavily_search import TavilySearchProvider as TavilyProvider

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key or api_key == "dummy_value":
            raise ValueError("TAVILY_API_KEY is required")

        self.max_results = max_results
        self.provider = TavilyProvider(
            api_key=api_key,
            max_results=max_results,
            include_answer=True,
        )

    async def search(self, query: str) -> SearchResult:
        """執行單一搜尋"""
        start = time.time()

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.provider.get_search_info(
                    query, max_results=self.max_results
                ),
            )

            elapsed = time.time() - start
            answer = result.get("answer", "")
            raw_results = result.get("results", [])

            return SearchResult(
                success=True,
                tool_type=self.provider_name,
                elapsed_time=elapsed,
                api_calls=1,
                data={"results": raw_results},
                raw_answer=answer,
                answer_length=len(answer),
            )
        except Exception as e:
            return SearchResult(
                success=False,
                tool_type=self.provider_name,
                elapsed_time=time.time() - start,
                api_calls=1,
                data={},
                raw_answer="",
                answer_length=0,
            )


# 全域實例
_tavily_provider = None


def get_tavily_provider() -> TavilySearchProvider:
    """取得 Tavily 提供者實例（單例）"""
    global _tavily_provider
    if _tavily_provider is None:
        _tavily_provider = TavilySearchProvider()
    return _tavily_provider


async def tavily_search(query: str) -> SearchResult:
    """便捷函式：執行 Tavily 搜尋"""
    provider = get_tavily_provider()
    return await provider.search(query)
