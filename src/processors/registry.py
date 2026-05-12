"""
Processor 註冊與查找

管理所有 Processor class 的註冊，支援裝飾器註冊與查找。
"""

from typing import Dict, Type, Optional
from .base import Processor

_registry: Dict[str, Type[Processor]] = {}


def register(processor_cls: Type[Processor]):
    """註冊 Processor（裝飾器用法）

    使用 processor_cls.processor_name 作為註冊鍵。
    可直接作為裝飾器使用：

        @register
        class MyProcessor(Processor):
            processor_name = "my_processor"
            ...
    """
    name = processor_cls.processor_name
    if not name:
        raise ValueError(
            f"Processor {processor_cls.__name__} 必須定義 processor_name"
        )
    _registry[name] = processor_cls
    return processor_cls


def get_processor(name: str) -> Optional[Type[Processor]]:
    """根據名稱取得 Processor class"""
    return _registry.get(name)


def list_processors() -> list[str]:
    """列出所有已註冊的 Processor 名稱"""
    return list(_registry.keys())
