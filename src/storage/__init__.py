"""
Storage 模組統一入口

提供全域唯一的 storage instance 管理：
- init_storage(config): 在 app 啟動時呼叫一次，依 config 決定建立哪種 Adapter
- get_storage():         所有 consumer 透過此函數取得 instance，不關心底層是誰
"""

import logging
from .factory import StorageFactory
from .base import StorageInterface

logger = logging.getLogger(__name__)

_instance: StorageInterface = None


def init_storage(config: dict) -> StorageInterface:
    """初始化 storage instance（全域唯一）

    Args:
        config: storage config dict，例如：
            {"type": "sqlite", "connection": "sqlite:///data/llm_responses.db"}
            或
            {"type": "dynamodb", "region": "ap-northeast-1",
             "llm_responses_table": "dev-llm-responses", ...}

    Returns:
        StorageInterface instance

    Raises:
        RuntimeError: 若已初始化過（防止重複 init）
    """
    global _instance
    if _instance is not None:
        logger.warning("Storage already initialized, skipping")
        return _instance

    _instance = StorageFactory.create(config)
    logger.info(f"Storage initialized: type={config.get('type')}")
    return _instance


def get_storage() -> StorageInterface:
    """取得全域唯一的 storage instance

    Returns:
        StorageInterface instance

    Raises:
        RuntimeError: 若尚未初始化
    """
    if _instance is None:
        raise RuntimeError(
            "Storage not initialized. Call init_storage() first."
        )
    return _instance


def is_initialized() -> bool:
    """檢查 storage 是否已初始化"""
    return _instance is not None
