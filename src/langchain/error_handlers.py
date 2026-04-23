# error_handlers.py
"""
錯誤處理包裝器模組

提供基於 LangChain 的重試與 Fallback 機制：
- RunnableRetry: 自動重試機制
- RunnableWithFallbacks: 多級 Fallback 機制
"""

import time
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar
from functools import wraps
import traceback
import inspect

try:
    from langchain_core.runnables import Runnable, RunnableConfig
    from langchain_core.runnables.utils import Input, Output
except ImportError:
    # 如果 LangChain 還未安裝，提供基本類型
    class Runnable:
        pass

    RunnableConfig = Dict[str, Any]
    Input = TypeVar("Input")
    Output = TypeVar("Output")

from .retry_config import (
    RetryConfig,
    FallbackConfig,
    get_retry_config,
    get_fallback_config,
)

logger = logging.getLogger(__name__)


class RetryableError(Exception):
    """可重試的錯誤"""

    def __init__(self, message: str, error_type: str, original_error: Exception = None):
        super().__init__(message)
        self.error_type = error_type
        self.original_error = original_error


class NonRetryableError(Exception):
    """不可重試的錯誤"""

    def __init__(self, message: str, error_type: str, original_error: Exception = None):
        super().__init__(message)
        self.error_type = error_type
        self.original_error = original_error


def classify_error(error: Exception) -> str:
    """
    分類錯誤類型

    Args:
        error: 異常物件

    Returns:
        str: 錯誤類型字串
    """
    error_name = type(error).__name__
    error_str = str(error).lower()
    error_details = getattr(error, "error", {}) or {}
    error_message = error_details.get("message", "") if isinstance(error_details, dict) else str(error_details)

    # 網路相關錯誤
    if "Timeout" in error_name or "timeout" in error_str:
        return "TimeoutError"
    elif "Connection" in error_name or "connection" in error_str:
        return "ConnectionError"

    # Gemini API 429 RESOURCE_EXHAUSTED
    if "resource_exhausted" in error_str or "RESOURCE_EXHAUSTED" in str(error):
        return "HTTPError(429)"

    # HTTP 狀態碼檢查
    if hasattr(error, "response") and hasattr(error.response, "status_code"):
        status_code = error.response.status_code
        if status_code == 429:
            return "HTTPError(429)"
        elif status_code == 503:
            return "HTTPError(503)"
        elif status_code == 401:
            return "AuthenticationError"
        elif status_code == 403:
            return "AuthenticationError"

    # 通用錯誤關鍵字
    if "rate limit" in error_str or "rate_limit" in error_str:
        return "RateLimitError"
    elif "auth" in error_str or "unauthorized" in error_str:
        return "AuthenticationError"
    elif "invalid" in error_str or "bad request" in error_str:
        return "InvalidRequestError"
    elif "validation" in error_str:
        return "ValidationError"
    elif "not found" in error_str or "404" in error_str:
        return "NotFoundError"
    elif "deadline" in error_str or "exceeded" in error_str:
        return "TimeoutError"

    # 預設為可重試的錯誤
    return "UnknownError"


class RunnableRetry:
    """
    可重試的 Runnable 包裝器

    提供自動重試功能，支援指數退避和錯誤分類
    """

    def __init__(
        self,
        runnable: Union[Callable, Runnable],
        retry_config: Optional[RetryConfig] = None,
        name: Optional[str] = None,
    ):
        """
        初始化重試包裝器

        Args:
            runnable: 要包裝的函式或 Runnable
            retry_config: 重試配置
            name: 包裝器名稱（用於日誌）
        """
        self.runnable = runnable
        self.retry_config = retry_config or get_retry_config()
        self.name = name or getattr(runnable, "__name__", "unknown")

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None) -> Any:
        """
        執行帶重試的同步調用

        Args:
            input: 輸入資料
            config: 執行配置

        Returns:
            Any: 執行結果

        Raises:
            NonRetryableError: 不可重試的錯誤
            RetryableError: 所有重試用盡後的錯誤
        """
        last_error = None
        total_start_time = time.time()

        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                logger.info(f"[{self.name}] 執行第 {attempt} 次嘗試")

                # 執行原始函式
                if hasattr(self.runnable, "invoke"):
                    result = self.runnable.invoke(input, config)
                else:
                    # 普通函式調用
                    if inspect.signature(self.runnable).parameters:
                        result = self.runnable(input)
                    else:
                        result = self.runnable()

                logger.info(f"[{self.name}] 第 {attempt} 次嘗試成功")
                return result

            except Exception as e:
                last_error = e
                error_type = classify_error(e)

                # 通用錯誤訊息提取
                def extract_clean_error(exc):
                    error_str = str(exc)
                    parts = []
                    
                    # 檢測是否為 API 錯誤結構 {"error": {"code": ..., "message": ..., "status": ...}}
                    if "'error':" in error_str or '"error":' in error_str:
                        try:
                            # 找 code
                            code = ""
                            if "'code':" in error_str:
                                code = error_str.split("'code':")[1].split(",")[0].strip()
                            elif '"code":' in error_str:
                                code = error_str.split('"code":')[1].split(",")[0].strip()
                            
                            # 找 message
                            message = ""
                            if "'message':" in error_str:
                                msg_part = error_str.split("'message':")[1]
                                if ", 'status'" in msg_part:
                                    message = msg_part.split(", 'status'")[0].strip()
                                elif ", \"status\"" in msg_part:
                                    message = msg_part.split(", \"status\"")[0].strip()
                                else:
                                    message = msg_part.split("}")[0].strip()
                            elif '"message":' in error_str:
                                msg_part = error_str.split('"message":')[1]
                                if ', "status"' in msg_part:
                                    message = msg_part.split(', "status"')[0].strip()
                                else:
                                    message = msg_part.split("}")[0].strip()
                            
                            # 找 status
                            status = ""
                            if "'status':" in error_str:
                                status = error_str.split("'status':")[1].split("}")[0].strip()
                            elif '"status":' in error_str:
                                status = error_str.split('"status":')[1].split("}")[0].strip()
                            
                            
                            # 組合簡潔訊息：code + status + message
                            if code and code.isdigit():
                                parts.append(f"({code})")
                            if status and status not in ["'UNKNOWN'", '"UNKNOWN"']:
                                parts.append(status.strip("'\""))
                            if message and message not in ["'Unknown'", '"Unknown"']:
                                msg_clean = message.strip("'\"")[:50]
                                if msg_clean:
                                    parts.append(msg_clean)
                            
                            if parts:
                                return " ".join(parts)
                        except (IndexError, AttributeError):
                            pass
                    
                    # 如果不是 API 錯誤結構或有問題，直接截取乾淨訊息
                    return error_str[:80] if error_str else error_type

                logger.warning(
                    f"[{self.name}] 第 {attempt} 次嘗試失敗: {error_type}"
                )

                # 檢查是否為不可重試的錯誤
                if not self.retry_config.is_retryable(error_type):
                    logger.error(f"[{self.name}] 不可重試的錯誤: {error_type}")
                    clean_msg = extract_clean_error(e)
                    raise NonRetryableError(
                        f"{error_type}: {clean_msg}",
                        error_type,
                        e
                    )

                # 檢查是否已達最大重試次數
                if attempt >= self.retry_config.max_attempts:
                    logger.error(
                        f"[{self.name}] 已達最大重試次數 {self.retry_config.max_attempts}"
                    )
                    raise RetryableError(
                        f"Max retries ({self.retry_config.max_attempts}) exceeded",
                        error_type,
                        e,
                    )

                # 檢查總時間是否超過限制
                if time.time() - total_start_time > self.retry_config.max_total_time:
                    logger.error(
                        f"[{self.name}] 總等待時間超過限制 {self.retry_config.max_total_time}秒"
                    )
                    raise RetryableError(
                        f"Total retry time exceeded {self.retry_config.max_total_time}s",
                        error_type,
                        e,
                    )

                # 計算等待時間並等待
                wait_time = self.retry_config.calculate_wait_time(attempt)
                logger.info(f"[{self.name}] 等待 {wait_time:.2f} 秒後重試")
                time.sleep(wait_time)

        # 不應該到達這裡，但為了安全起見
        raise RetryableError("Unexpected retry loop exit", "UnknownError", last_error)


class RunnableWithFallbacks:
    """
    帶 Fallback 的 Runnable 包裝器

    提供多級 Fallback 機制，主服務失敗時自動切換到備用服務
    """

    def __init__(
        self,
        primary_runnable: Union[Callable, Runnable],
        fallback_runnables: Dict[str, Union[Callable, Runnable]],
        fallback_config: Optional[FallbackConfig] = None,
        name: Optional[str] = None,
    ):
        """
        初始化 Fallback 包裝器

        Args:
            primary_runnable: 主要的函式或 Runnable
            fallback_runnables: Fallback 函式字典，key 為服務名稱
            fallback_config: Fallback 配置
            name: 包裝器名稱
        """
        self.primary_runnable = primary_runnable
        self.fallback_runnables = fallback_runnables
        self.fallback_config = fallback_config or get_fallback_config()
        self.name = name or getattr(primary_runnable, "__name__", "unknown")

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None) -> Any:
        """
        執行帶 Fallback 的調用

        Args:
            input: 輸入資料
            config: 執行配置

        Returns:
            Any: 執行結果

        Raises:
            Exception: 所有服務都失敗時的最後錯誤
        """
        last_error = None

        # 首先嘗試主要服務
        try:
            logger.info(f"[{self.name}] 嘗試主要服務")
            return self._invoke_runnable(self.primary_runnable, input, config)
        except Exception as e:
            last_error = e
            logger.warning(f"[{self.name}] 主要服務失敗: {str(e)}")

        # 依序嘗試 Fallback 服務
        for service_config in self.fallback_config.fallback_chain:
            service_name = service_config["service"]

            # 跳過主要服務（已經嘗試過）
            if service_name == "primary":
                continue

            if service_name not in self.fallback_runnables:
                logger.warning(f"[{self.name}] Fallback 服務 {service_name} 未註冊")
                continue

            try:
                logger.info(f"[{self.name}] 嘗試 Fallback 服務: {service_name}")
                runnable = self.fallback_runnables[service_name]
                result = self._invoke_runnable(runnable, input, config)
                logger.info(f"[{self.name}] Fallback 服務 {service_name} 成功")
                return result
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.name}] Fallback 服務 {service_name} 失敗: {str(e)}"
                )

        # 所有服務都失敗
        logger.error(f"[{self.name}] 所有服務（包含 Fallback）都失敗")
        if last_error:
            raise last_error
        else:
            raise Exception("All services failed")

    def _invoke_runnable(
        self,
        runnable: Union[Callable, Runnable],
        input: Any,
        config: Optional[RunnableConfig] = None,
    ) -> Any:
        """
        調用 Runnable 的統一介面

        Args:
            runnable: 要調用的函式或 Runnable
            input: 輸入資料
            config: 執行配置

        Returns:
            Any: 執行結果
        """
        if hasattr(runnable, "invoke"):
            return runnable.invoke(input, config)
        else:
            # 普通函式調用
            if inspect.signature(runnable).parameters:
                return runnable(input)
            else:
                return runnable()


def with_retry(
    retry_config: Optional[RetryConfig] = None,
    name: Optional[str] = None,
):
    """
    重試裝飾器

    Args:
        retry_config: 重試配置
        name: 函式名稱

    Returns:
        Callable: 裝飾後的函式
    """

    def decorator(func: Callable) -> Callable:
        retry_wrapper = RunnableRetry(func, retry_config, name or func.__name__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 將參數轉換為單一輸入
            if len(args) == 1 and not kwargs:
                input_data = args[0]
            else:
                input_data = {"args": args, "kwargs": kwargs}

            return retry_wrapper.invoke(input_data)

        return wrapper

    return decorator


def with_fallbacks(
    fallback_runnables: Dict[str, Union[Callable, Runnable]],
    fallback_config: Optional[FallbackConfig] = None,
    name: Optional[str] = None,
):
    """
    Fallback 裝飾器

    Args:
        fallback_runnables: Fallback 函式字典
        fallback_config: Fallback 配置
        name: 函式名稱

    Returns:
        Callable: 裝飾後的函式
    """

    def decorator(func: Callable) -> Callable:
        fallback_wrapper = RunnableWithFallbacks(
            func, fallback_runnables, fallback_config, name or func.__name__
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 將參數轉換為單一輸入
            if len(args) == 1 and not kwargs:
                input_data = args[0]
            else:
                input_data = {"args": args, "kwargs": kwargs}

            return fallback_wrapper.invoke(input_data)

        return wrapper

    return decorator


# 組合版本：同時具備重試和 Fallback 功能
class RunnableWithRetryAndFallbacks:
    """
    同時具備重試和 Fallback 功能的包裝器

    首先對主要服務應用重試機制，失敗後切換到 Fallback 服務，
    每個 Fallback 服務也會應用重試機制。
    """

    def __init__(
        self,
        primary_runnable: Union[Callable, Runnable],
        fallback_runnables: Dict[str, Union[Callable, Runnable]],
        retry_config: Optional[RetryConfig] = None,
        fallback_config: Optional[FallbackConfig] = None,
        name: Optional[str] = None,
    ):
        """
        初始化組合包裝器

        Args:
            primary_runnable: 主要的函式或 Runnable
            fallback_runnables: Fallback 函式字典
            retry_config: 重試配置
            fallback_config: Fallback 配置
            name: 包裝器名稱
        """
        # 將主要服務包裝為重試版本
        self.primary_retry = RunnableRetry(
            primary_runnable, retry_config, f"{name}_primary"
        )

        # 將 Fallback 服務都包裝為重試版本
        self.fallback_retries = {}
        for service_name, runnable in fallback_runnables.items():
            self.fallback_retries[service_name] = RunnableRetry(
                runnable, retry_config, f"{name}_{service_name}"
            )

        # 建立帶 Fallback 的包裝器
        self.fallback_wrapper = RunnableWithFallbacks(
            self.primary_retry, self.fallback_retries, fallback_config, name
        )

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None) -> Any:
        """
        執行帶重試和 Fallback 的調用

        Args:
            input: 輸入資料
            config: 執行配置

        Returns:
            Any: 執行結果
        """
        return self.fallback_wrapper.invoke(input, config)
