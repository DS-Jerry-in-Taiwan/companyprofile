# retry_config.py
"""
統一重試配置模組

定義統一的重試策略，包括：
- 最大重試次數
- 初始回退時間
- 最大回退時間
- 指數退避因子
- 可重試錯誤類型
"""

import time
from typing import List, Dict, Any, Type, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """錯誤類型枚舉"""

    TIMEOUT = "TimeoutError"
    CONNECTION = "ConnectionError"
    HTTP_503 = "HTTPError(503)"
    HTTP_429 = "HTTPError(429)"
    RATE_LIMIT = "RateLimitError"
    AUTH_ERROR = "AuthenticationError"
    INVALID_REQUEST = "InvalidRequestError"
    VALIDATION_ERROR = "ValidationError"


class RetryConfig:
    """重試配置類"""

    # 預設重試配置
    DEFAULT_CONFIG = {
        "max_attempts": 3,
        "initial_interval": 1.0,  # 秒
        "max_interval": 10.0,  # 秒
        "exponential_base": 2,
        "max_total_time": 60.0,  # 最大總等待時間（秒）
        "jitter": True,  # 是否加入隨機抖動
    }

    # 可重試的錯誤類型
    RETRYABLE_ERRORS = {
        ErrorType.TIMEOUT.value,
        ErrorType.CONNECTION.value,
        ErrorType.HTTP_503.value,
        ErrorType.HTTP_429.value,
        ErrorType.RATE_LIMIT.value,
    }

    # 不可重試的錯誤類型
    NON_RETRYABLE_ERRORS = {
        ErrorType.AUTH_ERROR.value,
        ErrorType.INVALID_REQUEST.value,
        ErrorType.VALIDATION_ERROR.value,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化重試配置

        Args:
            config: 自訂配置字典，會覆蓋預設值
        """
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

    @property
    def max_attempts(self) -> int:
        """最大重試次數"""
        return self.config["max_attempts"]

    @property
    def initial_interval(self) -> float:
        """初始重試間隔（秒）"""
        return self.config["initial_interval"]

    @property
    def max_interval(self) -> float:
        """最大重試間隔（秒）"""
        return self.config["max_interval"]

    @property
    def exponential_base(self) -> int:
        """指數退避底數"""
        return self.config["exponential_base"]

    @property
    def max_total_time(self) -> float:
        """最大總等待時間（秒）"""
        return self.config["max_total_time"]

    def is_retryable(self, error_type: str) -> bool:
        """
        檢查錯誤是否可重試

        Args:
            error_type: 錯誤類型字串

        Returns:
            bool: 是否可重試
        """
        return error_type in self.RETRYABLE_ERRORS

    def calculate_wait_time(self, attempt: int) -> float:
        """
        計算等待時間（指數退避）

        Args:
            attempt: 當前重試次數（從 1 開始）

        Returns:
            float: 等待時間（秒）
        """
        # 基本指數退避
        wait_time = self.initial_interval * (self.exponential_base ** (attempt - 1))

        # 限制最大等待時間
        wait_time = min(wait_time, self.max_interval)

        # 加入隨機抖動避免雪崩效應
        if self.config.get("jitter", True):
            import random

            jitter = random.uniform(0.8, 1.2)
            wait_time *= jitter

        return wait_time


class FallbackConfig:
    """Fallback 配置類"""

    # Fallback 服務鏈（按優先級排序）
    DEFAULT_FALLBACK_CHAIN = [
        {
            "service": "tavily",
            "priority": 1,
            "description": "Tavily API - 專業搜尋與內容提取",
            "timeout": 30,
        },
        {
            "service": "serper",
            "priority": 2,
            "description": "Serper API - Google 搜尋結果",
            "timeout": 30,
        },
        {
            "service": "web_search",
            "priority": 3,
            "description": "傳統爬蟲 - 直接爬取目標網站",
            "timeout": 30,
        },
        {
            "service": "mock",
            "priority": 4,
            "description": "Mock 資料 - 預設回應",
            "timeout": 1,
        },
    ]

    def __init__(self, fallback_chain: Optional[List[Dict[str, Any]]] = None):
        """
        初始化 Fallback 配置

        Args:
            fallback_chain: 自訂 Fallback 鏈，會覆蓋預設值
        """
        self.fallback_chain = fallback_chain or self.DEFAULT_FALLBACK_CHAIN.copy()
        self.fallback_chain.sort(key=lambda x: x["priority"])

    def get_next_service(self, failed_service: str) -> Optional[Dict[str, Any]]:
        """
        取得下一個 Fallback 服務

        Args:
            failed_service: 失敗的服務名稱

        Returns:
            Dict[str, Any] | None: 下一個服務的配置，如果沒有則回傳 None
        """
        failed_priority = None

        # 找出失敗服務的優先級
        for service in self.fallback_chain:
            if service["service"] == failed_service:
                failed_priority = service["priority"]
                break

        if failed_priority is None:
            # 如果沒找到失敗的服務，回傳第一個服務
            return self.fallback_chain[0] if self.fallback_chain else None

        # 找出下一個服務
        for service in self.fallback_chain:
            if service["priority"] > failed_priority:
                return service

        # 沒有下一個服務
        return None

    def get_all_services(self) -> List[str]:
        """取得所有服務名稱列表"""
        return [service["service"] for service in self.fallback_chain]


# 全域配置實例
default_retry_config = RetryConfig()
default_fallback_config = FallbackConfig()


def get_retry_config(custom_config: Optional[Dict[str, Any]] = None) -> RetryConfig:
    """
    取得重試配置實例

    Args:
        custom_config: 自訂配置字典

    Returns:
        RetryConfig: 重試配置實例
    """
    if custom_config:
        return RetryConfig(custom_config)
    return default_retry_config


def get_fallback_config(
    custom_chain: Optional[List[Dict[str, Any]]] = None,
) -> FallbackConfig:
    """
    取得 Fallback 配置實例

    Args:
        custom_chain: 自訂 Fallback 鏈

    Returns:
        FallbackConfig: Fallback 配置實例
    """
    if custom_chain:
        return FallbackConfig(custom_chain)
    return default_fallback_config
