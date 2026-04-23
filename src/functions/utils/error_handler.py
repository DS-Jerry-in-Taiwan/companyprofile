"""
錯誤處理模組 - 統一錯誤類型與格式

Phase20 錯誤處理標準化
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


# ===== 錯誤代碼枚舉 =====

class ErrorCode(Enum):
    """錯誤代碼枚舉"""

    # API 錯誤 (API_xxx)
    API_001 = ("API_001", 400, "Invalid request format", False)
    API_002 = ("API_002", 400, "Missing required field", False)
    API_003 = ("API_003", 400, "Invalid field value", False)
    API_004 = ("API_004", 401, "Authentication failed", False)
    API_005 = ("API_005", 403, "Permission denied", False)
    API_006 = ("API_006", 404, "Resource not found", False)
    API_007 = ("API_007", 422, "Validation failed", False)
    API_008 = ("API_008", 429, "Rate limit exceeded", True)
    API_009 = ("API_009", 500, "Internal server error", False)
    API_010 = ("API_010", 502, "Bad gateway", True)
    API_011 = ("API_011", 503, "Service unavailable", True)
    API_012 = ("API_012", 504, "Gateway timeout", True)

    # 服務錯誤 (SVC_xxx)
    SVC_001 = ("SVC_001", 500, "LLM API call failed", True)
    SVC_002 = ("SVC_002", 500, "Search timeout", True)
    SVC_003 = ("SVC_003", 404, "Search no results", False)
    SVC_004 = ("SVC_004", 500, "Summary generation failed", True)
    SVC_005 = ("SVC_005", 500, "Quality check failed", False)
    SVC_006 = ("SVC_006", 500, "Config loading failed", False)
    SVC_007 = ("SVC_007", 500, "State update failed", False)

    # LLM 錯誤 (LLM_xxx)
    LLM_001 = ("LLM_001", 429, "API quota exhausted", True)
    LLM_002 = ("LLM_002", 504, "Processing timeout", True)
    LLM_003 = ("LLM_003", 400, "Invalid request", False)
    LLM_004 = ("LLM_004", 401, "Authentication failed", False)
    LLM_005 = ("LLM_005", 429, "Quota exceeded", True)
    LLM_006 = ("LLM_006", 404, "Model not available", False)
    LLM_007 = ("LLM_007", 400, "Content filtered", False)
    LLM_008 = ("LLM_008", 500, "Unknown error", True)

    # 搜尋錯誤 (SCH_xxx)
    SCH_001 = ("SCH_001", 500, "Tavily API failed", True)
    SCH_002 = ("SCH_002", 500, "Gemini search failed", True)
    SCH_003 = ("SCH_003", 404, "No search results", False)
    SCH_004 = ("SCH_004", 206, "Partial results", True)
    SCH_005 = ("SCH_005", 400, "Search malformed", False)

    def __init__(self, code: str, http_status: int, message: str, retryable: bool):
        self.code = code
        self.http_status = http_status
        self.message = message
        self.retryable = retryable


# ===== 錯誤回應資料類別 =====

@dataclass
class ErrorDetail:
    """錯誤詳情"""
    code: str
    message: str
    details: Optional[str] = None
    source: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    recoverable: bool = False
    retry_after: Optional[int] = None


@dataclass
class ErrorResponse:
    """標準錯誤回應格式"""
    success: bool = False
    error: ErrorDetail = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {
            "success": self.success,
            "error": {
                "code": self.error.code,
                "message": self.error.message,
                "timestamp": self.error.timestamp,
            }
        }

        if self.error.details:
            result["error"]["details"] = self.error.details
        if self.error.source:
            result["error"]["source"] = self.error.source
        if self.error.request_id:
            result["error"]["request_id"] = self.error.request_id
        if self.error.trace_id:
            result["error"]["trace_id"] = self.error.trace_id
        if self.error.recoverable:
            result["error"]["recoverable"] = self.error.recoverable
        if self.error.retry_after:
            result["error"]["retry_after"] = self.error.retry_after

        return result


# ===== 自定義異常類別 =====

class ExternalServiceError(Exception):
    """外部服務錯誤"""
    def __init__(self, message: str, code: str = 'SVC_001', recoverable: bool = True):
        super().__init__(message)
        self.code = code
        self.message = message
        self.recoverable = recoverable


class LLMServiceError(Exception):
    """LLM 服務錯誤"""
    def __init__(self, message: str, code: str = 'LLM_008', recoverable: bool = True):
        super().__init__(message)
        self.code = code
        self.message = message
        self.recoverable = recoverable


class ValidationError(Exception):
    """驗證錯誤"""
    def __init__(self, message: str, code: str = 'API_007', details: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


# ===== 輔助函式 =====

def get_error_by_code(code: str) -> Optional[ErrorCode]:
    """根據錯誤代碼取得 ErrorCode枚舉值"""
    try:
        return ErrorCode[code]
    except KeyError:
        return None


def build_error_response(
    code: str,
    message: str,
    details: Optional[str] = None,
    source: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    recoverable: bool = False,
    retry_after: Optional[int] = None
) -> ErrorResponse:
    """建立標準錯誤回應"""
    error_detail = ErrorDetail(
        code=code,
        message=message,
        details=details,
        source=source,
        request_id=request_id,
        trace_id=trace_id,
        recoverable=recoverable,
        retry_after=retry_after
    )
    return ErrorResponse(success=False, error=error_detail)


def map_exception_to_error(exc: Exception) -> ErrorCode:
    """將異常對應到錯誤代碼"""
    exc_str = str(exc).lower()
    exc_type = type(exc).__name__

    # LLM 錯誤
    if "RESOURCE_EXHAUSTED" in str(exc) or "resource_exhausted" in exc_str:
        return ErrorCode.LLM_001
    if "DEADLINE_EXCEEDED" in str(exc) or "deadline" in exc_str:
        return ErrorCode.LLM_002
    if "UNAUTHENTICATED" in str(exc) or "auth" in exc_str:
        return ErrorCode.LLM_004
    if "QUOTA_EXCEEDED" in str(exc) or "quota" in exc_str:
        return ErrorCode.LLM_005
    if "NOT_FOUND" in str(exc) or "model" in exc_str:
        return ErrorCode.LLM_006

    # HTTP 錯誤
    if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
        status = exc.response.status_code
        if status == 429:
            return ErrorCode.API_008
        if status == 401:
            return ErrorCode.API_004
        if status == 403:
            return ErrorCode.API_005
        if status == 404:
            return ErrorCode.API_006
        if status == 500:
            return ErrorCode.API_009
        if status == 502:
            return ErrorCode.API_010
        if status == 503:
            return ErrorCode.API_011
        if status == 504:
            return ErrorCode.API_012

    # Timeout
    if "timeout" in exc_str or "Timeout" in exc_type:
        return ErrorCode.SVC_002

    # 預設
    return ErrorCode.LLM_008