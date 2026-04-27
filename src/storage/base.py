from abc import ABC, abstractmethod
from typing import Optional, List


class StorageInterface(ABC):
    """存储抽象接口"""

    @abstractmethod
    def save_response(self, item: dict) -> bool:
        """保存 LLM 响应"""
        pass

    @abstractmethod
    def get_response(self, request_id: str) -> Optional[dict]:
        """根据 request_id 获取响应"""
        pass

    @abstractmethod
    def list_by_organ(self, organ_no: str) -> list[dict]:
        """根据 organ_no 列表响应"""
        pass

    @abstractmethod
    def save_error(self, item: dict) -> bool:
        """保存錯誤日誌"""
        pass

    @abstractmethod
    def list_errors(self, limit: int = 100, error_code: str = None) -> list[dict]:
        """查詢錯誤日誌"""
        pass
