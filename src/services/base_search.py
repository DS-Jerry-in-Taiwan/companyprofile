"""
Base Search Provider - 搜尋抽象介面
Phase 2 - 數據檢索與前處理模組
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class SearchResult:
    """搜尋結果資料類別"""

    def __init__(self, url: str, title: str, snippet: str = ""):
        self.url = url
        self.title = title
        self.snippet = snippet

    def __repr__(self):
        return f"SearchResult(url='{self.url}', title='{self.title}')"


class BaseSearchProvider(ABC):
    """
    搜尋提供者的抽象基類
    所有搜尋實作必須繼承此類別
    """

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        執行搜尋並回傳結果列表

        Args:
            query: 搜尋關鍵字
            max_results: 最大回傳結果數量

        Returns:
            SearchResult 列表
        """
        pass

    @abstractmethod
    def handle_failure(self, query: str) -> None:
        """
        處理搜尋失敗的情况

        Args:
            query: 失敗的搜尋查詢
        """
        pass

    def filter_results(
        self, results: List[SearchResult], exclude_extensions: List[str] = None
    ) -> List[SearchResult]:
        """
        過濾搜尋結果，排除特定檔案類型

        Args:
            results: 原始搜尋結果
            exclude_extensions: 要排除的副檔名列表

        Returns:
            過濾後的結果列表
        """
        if exclude_extensions is None:
            exclude_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx"]

        filtered = []
        for result in results:
            url_lower = result.url.lower()
            if not any(url_lower.endswith(ext) for ext in exclude_extensions):
                filtered.append(result)

        return filtered
