from abc import ABC, abstractmethod
from typing import Optional


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
