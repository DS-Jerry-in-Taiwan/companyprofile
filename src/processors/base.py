"""
Processor 抽象類別

定義所有後處理 Processor 的統一介面。
"""

from abc import ABC, abstractmethod
from typing import Optional


class Processor(ABC):
    """後處理 Processor 抽象類別

    所有 Processor 必須繼承此類別並實作 process() 方法。
    subclass 需覆寫 processor_name class attribute 作為唯一識別名稱。
    """

    processor_name: str = ""  # subclass 覆寫此值

    @property
    def name(self) -> str:
        """Processor 唯一識別名稱，對應 config 中的 key"""
        return self.processor_name

    @abstractmethod
    def process(self, text: str, config: Optional[dict] = None) -> str:
        """處理文字，回傳處理後結果"""
        ...
