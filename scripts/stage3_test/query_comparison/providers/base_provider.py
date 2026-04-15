"""
搜尋提供者基底介面
==================

定義搜尋提供者的統一介面
使用主流程的 SearchResult dataclass
"""

# 路徑已在 providers/__init__.py 中設定
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from src.services.search_tools import SearchResult


class BaseSearchProvider(ABC):
    """搜尋提供者基底介面"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供者名稱"""
        pass

    @abstractmethod
    async def search(self, query: str) -> SearchResult:
        """
        執行單一搜尋

        Args:
            query: 搜尋查詢

        Returns:
            SearchResult: 統一的搜尋結果格式
        """
        pass
