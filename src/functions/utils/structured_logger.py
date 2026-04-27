#!/usr/bin/env python3
"""
結構化日誌模組
實作統一的結構化日誌格式，支援 request_id 追蹤、完整異常堆疊記錄
"""

import json
import uuid
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from logging import Logger
from contextlib import contextmanager
import threading

# 執行緒本地儲存，用於追蹤當前請求
_local = threading.local()


# 敏感欄位列表 - 記錄時應過濾
SENSITIVE_FIELDS = {"organNo", "password", "token", "secret", "api_key", "key"}

def _filter_sensitive_fields(data: Dict = None) -> Dict:
    """過濾敏感欄位"""
    if not data:
        return {}
    return {k: "***" if k.lower() in SENSITIVE_FIELDS else v 
            for k, v in data.items()}


class StructuredLogger:
    """結構化日誌記錄器"""

    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # 如果 root logger 已有 handler，則上傳到 root，不重複輸出
        if logging.getLogger().handlers:
            self.logger.propagate = True
            # 不再新增 handler
            return
            
        # 否則建立自己的 handler（只有 Lambda 環境才這麼做）
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # 設定格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 檔案處理器 (僅在非 Lambda 環境使用)
        # Lambda 環境會設置 AWS_EXECUTION_ENV 或 LAMBDA_TASK_ROOT
        import os

        if not os.environ.get("AWS_EXECUTION_ENV") and not os.environ.get(
            "LAMBDA_TASK_ROOT"
        ):
            # 本地開發環境才使用檔案處理器
            file_handler = logging.FileHandler("app_structured.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _get_request_context(self) -> Dict[str, Any]:
        """取得當前請求上下文"""
        return {
            "request_id": getattr(_local, "request_id", None),
            "trace_id": getattr(_local, "trace_id", None),
            "user_id": getattr(_local, "user_id", None),
            "session_id": getattr(_local, "session_id", None),
        }

    def _create_log_entry(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """建立標準化日誌條目"""
        log_entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "level": level,
            "system": kwargs.get("system", "OrganBriefOptimization"),
            "component": kwargs.get("component", "unknown"),
            "message": message,
            "context": self._get_request_context(),
        }

        # 移除 system 和 component 從 kwargs，避免重複
        kwargs.pop("system", None)
        kwargs.pop("component", None)

        # 添加額外資料
        if kwargs:
            log_entry["data"] = kwargs

        return log_entry

    def info(self, message: str, **kwargs):
        """記錄資訊層級日誌"""
        log_entry = self._create_log_entry("INFO", message, **kwargs)
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))

    def warning(self, message: str, **kwargs):
        """記錄警告層級日誌"""
        log_entry = self._create_log_entry("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(log_entry, ensure_ascii=False))

    def error(self, message: str, exception: Exception = None, **kwargs):
        """記錄錯誤層級日誌"""
        log_entry = self._create_log_entry("ERROR", message, **kwargs)

        if exception:
            log_entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "stacktrace": traceback.format_exc(),
            }

        self.logger.error(json.dumps(log_entry, ensure_ascii=False))

    def debug(self, message: str, **kwargs):
        """記錄除錯層級日誌"""
        log_entry = self._create_log_entry("DEBUG", message, **kwargs)
        self.logger.debug(json.dumps(log_entry, ensure_ascii=False))

    def api_request(self, method: str, path: str, request_data: Dict = None, **kwargs):
        """記錄 API 請求"""
        if "component" not in kwargs:
            kwargs["component"] = "api"
        # 過濾敏感欄位
        safe_data = _filter_sensitive_fields(request_data) if request_data else {}
        self.info(
            f"API Request: {method} {path}",
            method=method,
            path=path,
            request_data=safe_data,
            **kwargs,
        )

    def api_response(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time_ms: float,
        response_data: Dict = None,
        **kwargs,
    ):
        """記錄 API 回應"""
        if "component" not in kwargs:
            kwargs["component"] = "api"
        self.info(
            f"API Response: {method} {path} - {status_code}",
            method=method,
            path=path,
            status_code=status_code,
            response_time_ms=response_time_ms,
            response_data=response_data,
            **kwargs,
        )

    def external_api_call(
        self, service: str, method: str, url: str, request_data: Dict = None, **kwargs
    ):
        """記錄外部 API 呼叫"""
        if "component" not in kwargs:
            kwargs["component"] = "external_api"
        self.info(
            f"External API Call: {service} {method} {url}",
            service=service,
            method=method,
            url=url,
            request_data=request_data,
            **kwargs,
        )

    def external_api_response(
        self,
        service: str,
        method: str,
        url: str,
        status_code: int,
        response_time_ms: float,
        response_data: Dict = None,
        **kwargs,
    ):
        """記錄外部 API 回應"""
        if "component" not in kwargs:
            kwargs["component"] = "external_api"
        self.info(
            f"External API Response: {service} - {status_code}",
            service=service,
            method=method,
            url=url,
            status_code=status_code,
            response_time_ms=response_time_ms,
            response_data=response_data,
            **kwargs,
        )

    def database_operation(
        self, operation: str, table: str = None, duration_ms: float = None, **kwargs
    ):
        """記錄資料庫操作"""
        if "component" not in kwargs:
            kwargs["component"] = "database"
        self.info(
            f"Database Operation: {operation}",
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            **kwargs,
        )

    def business_event(
        self, event_name: str, entity_type: str = None, entity_id: str = None, **kwargs
    ):
        """記錄業務事件"""
        if "component" not in kwargs:
            kwargs["component"] = "business"
        self.info(
            f"Business Event: {event_name}",
            event_name=event_name,
            entity_type=entity_type,
            entity_id=entity_id,
            **kwargs,
        )


@contextmanager
def request_context(
    request_id: str = None,
    trace_id: str = None,
    user_id: str = None,
    session_id: str = None,
):
    """設定請求上下文"""
    # 生成 request_id 和 trace_id 如果未提供
    if not request_id:
        request_id = f"req-{uuid.uuid4().hex[:8]}"
    if not trace_id:
        trace_id = f"t-{uuid.uuid4().hex[:16]}"

    # 儲存原始值
    old_request_id = getattr(_local, "request_id", None)
    old_trace_id = getattr(_local, "trace_id", None)
    old_user_id = getattr(_local, "user_id", None)
    old_session_id = getattr(_local, "session_id", None)

    try:
        # 設定新值
        _local.request_id = request_id
        _local.trace_id = trace_id
        _local.user_id = user_id
        _local.session_id = session_id

        yield {
            "request_id": request_id,
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
        }
    finally:
        # 恢復原始值
        _local.request_id = old_request_id
        _local.trace_id = old_trace_id
        _local.user_id = old_user_id
        _local.session_id = old_session_id


def get_current_request_id() -> Optional[str]:
    """取得當前請求 ID"""
    return getattr(_local, "request_id", None)


def get_current_trace_id() -> Optional[str]:
    """取得當前追蹤 ID"""
    return getattr(_local, "trace_id", None)


class LogSearchAPI:
    """日誌搜尋 API 模擬實作"""

    def __init__(self, log_file_path: str = "app_structured.log"):
        self.log_file_path = log_file_path

    def search_logs(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """搜尋日誌"""
        # 模擬實作 - 實際環境中會連接到 ELK/Kafka 等
        try:
            logs = []
            with open(self.log_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.split(" - ", 3)[-1])
                        if self._matches_query(log_entry, query):
                            logs.append(log_entry)
                    except (json.JSONDecodeError, IndexError):
                        continue

            # 分頁處理
            page = query.get("page", 1)
            page_size = query.get("page_size", 50)
            start = (page - 1) * page_size
            end = start + page_size

            return {
                "logs": logs[start:end],
                "page": page,
                "page_size": page_size,
                "total": len(logs),
            }

        except FileNotFoundError:
            return {"logs": [], "page": 1, "total": 0}

    def _matches_query(self, log_entry: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """檢查日誌是否符合查詢條件"""
        # 時間範圍檢查
        if "start_time" in query or "end_time" in query:
            log_time = log_entry.get("timestamp")
            if log_time:
                if "start_time" in query and log_time < query["start_time"]:
                    return False
                if "end_time" in query and log_time > query["end_time"]:
                    return False

        # 追蹤 ID 檢查
        if "trace_id" in query:
            log_trace_id = log_entry.get("context", {}).get("trace_id")
            if log_trace_id != query["trace_id"]:
                return False

        # 請求 ID 檢查
        if "request_id" in query:
            log_request_id = log_entry.get("context", {}).get("request_id")
            if log_request_id != query["request_id"]:
                return False

        # 層級檢查
        if "level" in query:
            if log_entry.get("level") != query["level"]:
                return False

        # 系統檢查
        if "system" in query:
            if log_entry.get("system") != query["system"]:
                return False

        # 關鍵字搜尋
        if "keyword" in query:
            keyword = query["keyword"].lower()
            message = log_entry.get("message", "").lower()
            if keyword not in message:
                return False

        return True


# 全域日誌器實例
structured_logger = StructuredLogger("organ_brief_optimization")
log_search_api = LogSearchAPI()


# 簡化的函數介面
def log_info(message: str, **kwargs):
    structured_logger.info(message, **kwargs)


def log_warning(message: str, **kwargs):
    structured_logger.warning(message, **kwargs)


def log_error(message: str, exception: Exception = None, **kwargs):
    structured_logger.error(message, exception=exception, **kwargs)


def log_debug(message: str, **kwargs):
    structured_logger.debug(message, **kwargs)


def log_api_request(method: str, path: str, request_data: Dict = None, **kwargs):
    structured_logger.api_request(method, path, request_data, **kwargs)


def log_api_response(
    method: str,
    path: str,
    status_code: int,
    response_time_ms: float,
    response_data: Dict = None,
    **kwargs,
):
    structured_logger.api_response(
        method, path, status_code, response_time_ms, response_data, **kwargs
    )


def log_external_api_call(
    service: str, method: str, url: str, request_data: Dict = None, **kwargs
):
    structured_logger.external_api_call(service, method, url, request_data, **kwargs)


def log_external_api_response(
    service: str,
    method: str,
    url: str,
    status_code: int,
    response_time_ms: float,
    response_data: Dict = None,
    **kwargs,
):
    structured_logger.external_api_response(
        service, method, url, status_code, response_time_ms, response_data, **kwargs
    )


def search_logs(query: Dict[str, Any]) -> Dict[str, Any]:
    """搜尋日誌"""
    return log_search_api.search_logs(query)
