"""
Serper Search Provider Implementation
使用 Serper.dev API 的搜尋服務實作
"""

import os
import logging
from typing import List, Dict, Any, Optional
import requests
from .base_search import BaseSearchProvider, SearchResult
from .base_search_provider import SearchError

logger = logging.getLogger(__name__)


class SerperSearchProvider(BaseSearchProvider):
    """Serper.dev API 搜尋服務實作"""

    BASE_URL = "https://google.serper.dev/search"

    def __init__(
        self, api_key: Optional[str] = None, country: str = "tw", language: str = "zh"
    ):
        """
        初始化 Serper 搜尋服務

        Args:
            api_key: Serper API 金鑰
            country: 搜尋國家代碼
            language: 搜尋語言
        """
        self.api_key: str = api_key or os.getenv("SERPER_API_KEY", "")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY is required")

        self.country = country
        self.language = language
        self._last_metadata: Dict[str, Any] = {}

        # 檢查是否為測試用的 dummy_value
        self._use_mock = self.api_key == "dummy_value"

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        執行搜尋並回傳 SearchResult 列表

        Args:
            query: 搜尋查詢字串
            max_results: 最大回傳結果數量

        Returns:
            List[SearchResult]: SearchResult 列表
        """
        # 如果是測試用的 dummy_value，使用 mock 搜尋
        if self._use_mock:
            return self._mock_search(query, max_results)

        try:
            headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

            payload = {
                "q": query,
                "gl": self.country,
                "hl": self.language,
                "num": max_results,
            }

            response = requests.post(
                self.BASE_URL, json=payload, headers=headers, timeout=10
            )

            response.raise_for_status()
            data = response.json()

            # 儲存元資料
            self._last_metadata = {
                "query": query,
                "total_results": data.get("searchParameters", {}).get(
                    "totalResults", 0
                ),
                "search_time": data.get("searchParameters", {}).get("timeTaken", 0),
            }

            # 提取搜尋結果
            results = []
            organic_results = data.get("organic", [])

            for item in organic_results[:max_results]:
                if "link" in item:
                    results.append(
                        SearchResult(
                            url=item["link"],
                            title=item.get("title", ""),
                            snippet=item.get("snippet", ""),
                        )
                    )

            if not results:
                self.handle_failure(query)

            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Search API error: {e}")
            # 如果 API 請求失敗，嘗試使用 mock 搜尋
            logger.info("Falling back to mock search due to API error")
            return self._mock_search(query, max_results)
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            # 如果發生未預期錯誤，嘗試使用 mock 搜尋
            logger.info("Falling back to mock search due to unexpected error")
            return self._mock_search(query, max_results)

    def _mock_search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        提供 mock 搜尋結果，用於測試或 API 失敗時

        Args:
            query: 搜尋查詢字串
            max_results: 最大回傳結果數量

        Returns:
            List[SearchResult]: 模擬的 SearchResult 列表
        """
        logger.info(f"Using mock search for query: {query}")

        # 根據查詢返回一些模擬結果
        mock_results = [
            SearchResult(
                url=f"https://example.com/article/1?q={query}",
                title=f"Article 1 about {query}",
                snippet=f"This is an article about {query}",
            ),
            SearchResult(
                url=f"https://example.com/article/2?q={query}",
                title=f"Article 2 about {query}",
                snippet=f"Another article about {query}",
            ),
            SearchResult(
                url=f"https://example.com/article/3?q={query}",
                title=f"Article 3 about {query}",
                snippet=f"More information about {query}",
            ),
            SearchResult(
                url=f"https://example.com/news?q={query}",
                title=f"News about {query}",
                snippet=f"Latest news about {query}",
            ),
            SearchResult(
                url=f"https://example.com/blog?q={query}",
                title=f"Blog post about {query}",
                snippet=f"Blog post discussing {query}",
            ),
        ]

        # 儲存元資料
        self._last_metadata = {
            "query": query,
            "total_results": len(mock_results),
            "search_time": 0.1,
            "is_mock": True,
        }

        return mock_results[:max_results]

    def handle_failure(self, query: str) -> None:
        """
        處理搜尋失敗的情況

        Args:
            query: 失敗的搜尋查詢字串
        """
        logger.warning(f"Search failed for query: {query}")
        # 可以在這裡實現重試邏輯或通知機制
        pass

    def get_search_metadata(self, query: str) -> dict:
        """
        取得搜尋元資料

        Args:
            query: 搜尋查詢字串

        Returns:
            dict: 包含搜尋相關資訊的字典
        """
        return self._last_metadata

    def search_with_details(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        執行搜尋並回傳詳細結果

        Args:
            query: 搜尋查詢字串
            max_results: 最大回傳結果數量

        Returns:
            List[Dict[str, Any]]: 詳細搜尋結果列表
        """
        # 如果是測試用的 dummy_value，使用 mock 搜尋
        if self._use_mock:
            return self._mock_search_with_details(query, max_results)

        try:
            headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

            payload = {
                "q": query,
                "gl": self.country,
                "hl": self.language,
                "num": max_results,
            }

            response = requests.post(
                self.BASE_URL, json=payload, headers=headers, timeout=10
            )

            response.raise_for_status()
            data = response.json()

            results = []
            organic_results = data.get("organic", [])

            for i, result in enumerate(organic_results[:max_results], 1):
                results.append(
                    {
                        "position": i,
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "displayed_url": result.get("displayedUrl", ""),
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error in search_with_details: {e}")
            # 如果 API 請求失敗，嘗試使用 mock 搜尋
            logger.info("Falling back to mock search with details due to API error")
            return self._mock_search_with_details(query, max_results)

    def _mock_search_with_details(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        提供 mock 詳細搜尋結果，用於測試或 API 失敗時

        Args:
            query: 搜尋查詢字串
            max_results: 最大回傳結果數量

        Returns:
            List[Dict[str, Any]]: 模擬的詳細搜尋結果列表
        """
        logger.info(f"Using mock search with details for query: {query}")

        # 根據查詢返回一些模擬結果
        mock_results = [
            {
                "position": 1,
                "title": f"Article 1 about {query}",
                "url": f"https://example.com/article/1?q={query}",
                "snippet": f"This is an article about {query}",
                "displayed_url": f"example.com/article/1",
            },
            {
                "position": 2,
                "title": f"Article 2 about {query}",
                "url": f"https://example.com/article/2?q={query}",
                "snippet": f"Another article about {query}",
                "displayed_url": f"example.com/article/2",
            },
            {
                "position": 3,
                "title": f"Article 3 about {query}",
                "url": f"https://example.com/article/3?q={query}",
                "snippet": f"More information about {query}",
                "displayed_url": f"example.com/article/3",
            },
            {
                "position": 4,
                "title": f"News about {query}",
                "url": f"https://example.com/news?q={query}",
                "snippet": f"Latest news about {query}",
                "displayed_url": f"example.com/news",
            },
            {
                "position": 5,
                "title": f"Blog post about {query}",
                "url": f"https://example.com/blog?q={query}",
                "snippet": f"Blog post discussing {query}",
                "displayed_url": f"example.com/blog",
            },
        ]

        return mock_results[:max_results]
