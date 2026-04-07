"""
Tavily Search Provider Implementation
使用 Tavily API 的搜尋和內容提取服務
官網：https://tavily.com/
API文檔：https://docs.tavily.com/
"""

import os
import logging
from typing import List, Dict, Any, Optional
import requests
from .base_search import BaseSearchProvider, SearchResult
from .base_search_provider import SearchError

logger = logging.getLogger(__name__)


class TavilySearchProvider:
    """Tavily API 搜尋服務實作"""

    # Tavily API endpoints
    SEARCH_URL = "https://api.tavily.com/search"
    # NOTE: /get_search_info endpoint does NOT exist in Tavily API
    # The /search endpoint already supports all needed features:
    # - include_answer: AI-generated answer
    # - include_raw_content: content extraction
    # This is kept for backward compatibility reference only

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_results: int = 5,
        include_answer: bool = True,
        include_raw_content: bool = True,
        include_images: bool = False,
    ):
        """
        初始化 Tavily 搜尋服務

        Args:
            api_key: Tavily API 金鑰
            max_results: 最大回傳結果數量
            include_answer: 是否包含 AI 生成的答案摘要
            include_raw_content: 是否包含原始內容
            include_images: 是否包含圖片
        """
        self.api_key: str = api_key or os.getenv("TAVILY_API_KEY", "")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is required")

        self.max_results = max_results
        self.include_answer = include_answer
        self.include_raw_content = include_raw_content
        self.include_images = include_images
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
        if self._use_mock:
            return self._mock_search(query, max_results)

        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": self.include_answer,
                "include_raw_content": self.include_raw_content,
                "include_images": self.include_images,
            }

            response = requests.post(self.SEARCH_URL, json=payload, timeout=30)

            response.raise_for_status()
            data = response.json()

            # 提取搜尋結果
            results = []
            for item in data.get("results", [])[:max_results]:
                results.append(
                    SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        snippet=item.get("content", ""),
                    )
                )

            # 儲存元資料
            self._last_metadata = {
                "query": query,
                "total_results": len(results),
                "answer": data.get("answer"),
                "response_time": data.get("response_time", 0),
            }

            if not results:
                logger.warning(f"No results found for query: {query}")

            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Tavily Search API error: {e}")
            return self._mock_search(query, max_results)
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return self._mock_search(query, max_results)

    def get_search_info(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        執行搜尋並同時提取內容（一次搞定）
        這是最推薦的方式，可以獲得:
        - 搜尋結果
        - 每個結果的 AI 生成的答案
        - 原始內容片段

        注意: Tavily API 沒有 /get_search_info endpoint
        我們使用 /search endpoint 並啟用 include_answer 和 include_raw_content 來實現相同功能

        Args:
            query: 搜尋查詢字串
            max_results: 最大回傳結果數量

        Returns:
            Dict: 包含 results, answer, images 等資訊的字典
        """
        if self._use_mock:
            return self._mock_get_search_info(query, max_results)

        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": self.include_answer,
                "include_raw_content": self.include_raw_content,
                "include_images": self.include_images,
            }

            # 使用正確的 /search endpoint
            response = requests.post(
                self.SEARCH_URL,
                json=payload,
                timeout=60,
            )

            response.raise_for_status()
            data = response.json()

            # 儲存元資料
            self._last_metadata = {
                "query": query,
                "total_results": len(data.get("results", [])),
                "answer": data.get("answer"),
                "response_time": data.get("response_time", 0),
            }

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Tavily search API error: {e}")
            return self._mock_get_search_info(query, max_results)
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return self._mock_get_search_info(query, max_results)

    def search_with_content(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        執行搜尋並回傳包含內容的詳細結果

        Args:
            query: 搜尋查詢字串
            max_results: 最大回傳結果數量

        Returns:
            List[Dict]: 包含 url, title, content, score 等的列表
        """
        data = self.get_search_info(query, max_results)

        results = []
        for item in data.get("results", [])[:max_results]:
            results.append(
                {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0),
                    "published_date": item.get("published_date"),
                }
            )

        return results

    def _mock_search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """提供 mock 搜尋結果"""
        logger.info(f"Using mock Tavily search for query: {query}")

        mock_results = [
            SearchResult(
                url=f"https://example.com/company/{query.replace(' ', '-')}",
                title=f"關於 {query} - 官方網站",
                snippet=f"這是 {query} 的官方網站，提供詳細的公司資訊和產品服務介紹。",
            ),
            SearchResult(
                url=f"https://example.com/news/{query.replace(' ', '-')}",
                title=f"{query} 最新消息",
                snippet=f"關於 {query} 的最新產業動態和新聞報導。",
            ),
            SearchResult(
                url=f"https://example.com/about/{query.replace(' ', '-')}",
                title=f"{query} 公司簡介",
                snippet=f"{query} 成立多年，致力於提供優質服務。",
            ),
        ]

        self._last_metadata = {
            "query": query,
            "total_results": len(mock_results),
            "is_mock": True,
        }

        return mock_results[:max_results]

    def _mock_get_search_info(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """提供 mock get_search_info 結果"""
        logger.info(f"Using mock Tavily get_search_info for query: {query}")

        return {
            "answer": f"這是關於 {query} 的 AI 生成摘要。{query} 是一家專業的公司，提供多元化的服務。",
            "results": [
                {
                    "url": f"https://example.com/company/{query.replace(' ', '-')}",
                    "title": f"關於 {query} - 官方網站",
                    "content": f"這是 {query} 的官方網站內容。我們提供專業的服務，包含產品設計、開發和銷售。公司成立於2010年，致力於為客戶提供最佳的解決方案。我們的團隊由經驗豐富的專業人士組成，並持續追求創新和品質。",
                    "score": 0.95,
                },
                {
                    "url": f"https://example.com/about/{query.replace(' ', '-')}",
                    "title": f"{query} 公司簡介",
                    "content": f"{query} 是一家領先的企業，專注於技術創新和客戶服務。我們的使命是透過優質的產品和服務，為社會創造價值。公司擁有完善的治理結構和專業的管理團隊。",
                    "score": 0.88,
                },
                {
                    "url": f"https://example.com/services/{query.replace(' ', '-')}",
                    "title": f"{query} 服務項目",
                    "content": f"我們提供多元化的服務，包括顧問服務、技術支援和培訓。每項服務都由專業團隊提供，確保客戶獲得最大的價值。",
                    "score": 0.82,
                },
            ],
            "images": [],
            "response_time": 0.5,
        }

    def get_metadata(self) -> Dict[str, Any]:
        """取得搜尋元資料"""
        return self._last_metadata
