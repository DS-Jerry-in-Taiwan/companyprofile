"""
Base Search Provider Abstract Class
定義搜尋服務的抽象介面，支援不同搜尋 API 的實作
"""

from abc import ABC, abstractmethod
from typing import List


class BaseSearchProvider(ABC):
    """搜尋服務的抽象基礎類別"""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[str]:
        """
        執行搜尋並回傳 URL 列表

        Args:
            query: 搜尋查詢字串
            max_results: 最大回傳結果數量

        Returns:
            List[str]: URL 列表

        Raises:
            SearchError: 搜尋失敗時拋出
        """
        pass

    @abstractmethod
    def handle_failure(self, query: str) -> None:
        """
        處理搜尋失敗的情況

        Args:
            query: 失敗的搜尋查詢字串
        """
        pass

    @abstractmethod
    def get_search_metadata(self, query: str) -> dict:
        """
        取得搜尋元資料

        Args:
            query: 搜尋查詢字串

        Returns:
            dict: 包含搜尋相關資訊的字典
        """
        pass


class SearchError(Exception):
    """搜尋服務錯誤"""

    def __init__(self, message: str, query: str = "", provider: str = ""):
        self.message = message
        self.query = query
        self.provider = provider
        super().__init__(self.message)
