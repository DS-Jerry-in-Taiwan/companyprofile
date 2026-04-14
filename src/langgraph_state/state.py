# state.py
"""
LangGraph 狀態定義模組

定義公司簡介生成流程的狀態結構和節點類型，支援動態路由和錯誤處理。
"""

import logging
from typing import Dict, Any, List, Optional, TypedDict, Union, Literal
from dataclasses import dataclass, field
from datetime import datetime

try:
    from langgraph.graph import StateGraph, Graph
    from langchain_core.runnables import Runnable
    from typing_extensions import NotRequired

    LANGGRAPH_AVAILABLE = True
except ImportError:
    # 如果 LangGraph 還未安裝，提供基本類型
    StateGraph = object
    Graph = object
    Runnable = object
    NotRequired = object
    LANGGRAPH_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===== 狀態類型定義 =====


class NodeStatus(str):
    """節點執行狀態枚舉"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ErrorSeverity(str):
    """錯誤嚴重程度枚舉"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NodeResult:
    """節點執行結果"""

    node_name: str
    status: NodeStatus
    output: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """錯誤資訊"""

    error_type: str
    error_message: str
    node_name: str
    severity: ErrorSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    original_error: Optional[Exception] = None
    retry_count: int = 0
    is_retryable: bool = True


@dataclass
class SearchResult:
    """搜尋結果"""

    success: bool
    answer: Optional[str] = None
    results: List[Dict[str, Any]] = field(default_factory=list)
    source: str = "unknown"  # tavily, web_search, mock
    execution_time: float = 0.0
    error: Optional[str] = None


@dataclass
class LLMResult:
    """LLM 生成結果"""

    success: bool
    title: Optional[str] = None
    body_html: Optional[str] = None
    summary: Optional[str] = None
    execution_time: float = 0.0
    error: Optional[str] = None


@dataclass
class QualityCheckResult:
    """品質檢查結果"""

    passed: bool
    score: float = 0.0
    issues: List[Dict[str, str]] = field(default_factory=list)
    suggestions: List[Dict[str, str]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


# Phase 14 Stage 3: 字數檢核結果
@dataclass
class WordCountValidationResult:
    """字數檢核結果"""

    is_valid: bool = False  # 是否在範圍內
    word_count: int = 0  # 實際字數
    min_range: int = 0  # 最小範圍
    max_range: int = 0  # 最大範圍
    needs_rewrite: bool = False  # 是否需要重寫
    rewrite_reason: Optional[str] = None  # 重寫原因
    rewrite_count: int = 0  # 已重寫次數
    rewrite_successful: bool = False  # 重寫是否成功
    final_word_count: int = 0  # 最終字數（重寫後）
    warnings: List[str] = field(default_factory=list)  # 警告訊息


# ===== 狀態圖狀態定義 =====


class CompanyBriefState(TypedDict):
    """公司簡介生成狀態圖的狀態"""

    # 輸入資料
    organ: str
    organ_no: Optional[str]
    company_url: Optional[str]
    user_brief: Optional[str]
    word_limit: Optional[int]  # Phase 11 新增
    # Phase 14: 新增選填欄位
    capital: Optional[int]  # 資本額
    employees: Optional[int]  # 員工人數
    founded_year: Optional[int]  # 成立年份
    # Phase 14 Stage 2: 模板類型 (concise/standard/detailed)
    optimization_mode: Optional[str]
    # Phase 14 Stage 3: 最大重寫次數（字數檢核）
    max_rewrite_attempts: int

    # 執行狀態
    current_node: str
    execution_path: List[str]
    retry_counts: Dict[str, int]

    # 中間結果
    search_result: Optional[SearchResult]
    llm_result: Optional[LLMResult]
    quality_check_result: Optional[QualityCheckResult]
    # Phase 14 Stage 3: 字數檢核結果
    word_count_validation: Optional[WordCountValidationResult]

    # 最終結果
    final_result: Optional[Dict[str, Any]]

    # 錯誤處理
    errors: List[ErrorInfo]
    current_error: Optional[ErrorInfo]

    # 元數據
    start_time: datetime
    total_execution_time: float
    metadata: Dict[str, Any]


# ===== 節點名稱常數 =====


class NodeNames:
    """節點名稱常數"""

    # 基本節點
    START = "start"
    END = "end"

    # 功能節點
    SEARCH = "search"
    GENERATE = "generate"
    QUALITY_CHECK = "quality_check"

    # 錯誤處理節點
    ERROR_HANDLER = "error_handler"
    RETRY_SEARCH = "retry_search"
    RETRY_GENERATE = "retry_generate"
    FALLBACK_SEARCH = "fallback_search"

    # 決策節點
    ROUTE_AFTER_SEARCH = "route_after_search"
    ROUTE_AFTER_GENERATE = "route_after_generate"
    ROUTE_AFTER_QUALITY = "route_after_quality"


# ===== 邊條件常數 =====


class EdgeConditions:
    """邊條件常數"""

    # 成功路徑
    SUCCESS = "success"
    FAILED = "failed"

    # 搜尋結果
    SEARCH_SUCCESS = "search_success"
    SEARCH_FAILED = "search_failed"

    # LLM 結果
    GENERATE_SUCCESS = "generate_success"
    GENERATE_FAILED = "generate_failed"

    # 品質檢查結果
    QUALITY_PASSED = "quality_passed"
    QUALITY_FAILED = "quality_failed"

    # 重試決策
    RETRY = "retry"
    NO_RETRY = "no_retry"
    FALLBACK = "fallback"

    # 錯誤處理
    RECOVERABLE = "recoverable"
    UNRECOVERABLE = "unrecoverable"


# ===== 狀態操作函式 =====


def create_initial_state(
    organ: str,
    organ_no: Optional[str] = None,
    company_url: Optional[str] = None,
    user_brief: Optional[str] = None,
    word_limit: Optional[int] = None,
    capital: Optional[int] = None,
    employees: Optional[int] = None,
    founded_year: Optional[int] = None,
    optimization_mode: Optional[str] = None,
    max_rewrite_attempts: int = 2,  # Phase 14 Stage 3: 最大重寫次數
) -> CompanyBriefState:
    """
    建立初始狀態

    Args:
        organ: 公司名稱
        organ_no: 統一編號
        company_url: 公司官網
        user_brief: 用戶簡介
        word_limit: 字數限制（Phase 11 新增）
        capital: 資本額（Phase 14 新增）
        employees: 員工人數（Phase 14 新增）
        founded_year: 成立年份（Phase 14 新增）
        optimization_mode: 模板類型 (concise/standard/detailed)（Phase 14 Stage 2 新增）
        max_rewrite_attempts: 最大重寫次數（Phase 14 Stage 3 新增）

    Returns:
        CompanyBriefState: 初始狀態
    """
    return CompanyBriefState(
        # 輸入資料
        organ=organ,
        organ_no=organ_no,
        company_url=company_url,
        user_brief=user_brief,
        word_limit=word_limit,
        capital=capital,
        employees=employees,
        founded_year=founded_year,
        optimization_mode=optimization_mode,
        max_rewrite_attempts=max_rewrite_attempts,
        # 執行狀態
        current_node=NodeNames.START,
        execution_path=[],
        retry_counts={},
        # 中間結果
        search_result=None,
        llm_result=None,
        quality_check_result=None,
        word_count_validation=None,  # Phase 14 Stage 3 新增
        # 最終結果
        final_result=None,
        # 錯誤處理
        errors=[],
        current_error=None,
        # 元數據
        start_time=datetime.now(),
        total_execution_time=0.0,
        metadata={},
    )


def update_state_with_node_result(
    state: CompanyBriefState,
    node_result: NodeResult,
) -> CompanyBriefState:
    """
    根據節點執行結果更新狀態

    Args:
        state: 當前狀態
        node_result: 節點執行結果

    Returns:
        CompanyBriefState: 更新後的狀態
    """
    # 更新執行路徑
    state["execution_path"] = state["execution_path"] + [node_result.node_name]
    state["current_node"] = node_result.node_name

    # 處理錯誤
    if node_result.error:
        error_info = ErrorInfo(
            error_type=type(node_result.error).__name__,
            error_message=str(node_result.error),
            node_name=node_result.node_name,
            severity=ErrorSeverity.HIGH,
            original_error=node_result.error,
        )
        state["errors"] = state["errors"] + [error_info]
        state["current_error"] = error_info
    else:
        state["current_error"] = None

    # 根據節點類型更新結果
    if (
        node_result.node_name in [NodeNames.SEARCH, NodeNames.FALLBACK_SEARCH]
        and node_result.output
    ):
        state["search_result"] = node_result.output
    elif (
        node_result.node_name in [NodeNames.GENERATE, NodeNames.RETRY_GENERATE]
        and node_result.output
    ):
        state["llm_result"] = node_result.output
    elif node_result.node_name == NodeNames.QUALITY_CHECK and node_result.output:
        state["quality_check_result"] = node_result.output

    return state


def should_retry_node(
    state: CompanyBriefState, node_name: str, max_retries: int = 3
) -> bool:
    """
    檢查節點是否應該重試

    Args:
        state: 當前狀態
        node_name: 節點名稱
        max_retries: 最大重試次數

    Returns:
        bool: 是否應該重試
    """
    current_retries = state["retry_counts"].get(node_name, 0)

    # 檢查是否超過最大重試次數
    if current_retries >= max_retries:
        return False

    # 檢查是否有可重試的錯誤
    if state["current_error"] and state["current_error"].is_retryable:
        return True

    return False


def increment_retry_count(
    state: CompanyBriefState, node_name: str
) -> CompanyBriefState:
    """
    增加節點重試計數

    Args:
        state: 當前狀態
        node_name: 節點名稱

    Returns:
        CompanyBriefState: 更新後的狀態
    """
    retry_counts = state["retry_counts"].copy()
    retry_counts[node_name] = retry_counts.get(node_name, 0) + 1
    state["retry_counts"] = retry_counts

    return state


def finalize_state(
    state: CompanyBriefState, final_result: Dict[str, Any]
) -> CompanyBriefState:
    """
    完成狀態，設置最終結果

    Phase 14 Stage 3 更新：整合字數檢核和重寫邏輯
    - 預設模式：輕量驗證，不強制截斷
    - 由 word_count_validator 負責檢核和重寫觸發
    - 重寫由調用方透過 LLM 執行

    Args:
        state: 當前狀態
        final_result: 最終結果

    Returns:
        CompanyBriefState: 完成的狀態
    """
    # Phase 11: 應用字數截斷
    word_limit = state.get("word_limit")

    # Phase 14 Stage 2: 應用模板差異化（differentiate_template）
    # 根據 optimization_mode 截斷到對應的模板長度限制
    optimization_mode = state.get("optimization_mode", "standard")
    # 對應 template_type (concise/standard/detailed)
    template_type = optimization_mode.lower() if optimization_mode else "standard"

    # Phase 14 Stage 3: 字數檢核結果初始化
    word_count_validation_result = None
    max_rewrite_attempts = state.get("max_rewrite_attempts", 2)

    if final_result:
        try:
            import sys
            import os

            PROJECT_ROOT = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
            if PROJECT_ROOT not in sys.path:
                sys.path.insert(0, PROJECT_ROOT)

            from src.functions.utils.template_differentiator import (
                differentiate_template,
            )
            from src.functions.utils.word_count_validator import (
                WordCountValidator,
                # WordCountValidationResult is defined in state.py itself (line 114)
            )

            # Phase 14 Stage 3: 字數檢核
            body_html = final_result.get("body_html", "")
            if body_html:
                validator = WordCountValidator()
                validation = validator.validate(body_html, template_type)

                # 建立檢核結果
                word_count_validation_result = WordCountValidationResult(
                    is_valid=validation.is_valid,
                    word_count=validation.word_count,
                    min_range=validation.min_range,
                    max_range=validation.max_range,
                    needs_rewrite=validation.needs_rewrite,
                    rewrite_reason=validation.rewrite_reason,
                    rewrite_count=0,
                    rewrite_successful=False,
                    final_word_count=validation.word_count,
                    warnings=[],
                )

                # 如果需要重寫，記錄警告（重寫由調用方執行）
                if validation.needs_rewrite:
                    logger.warning(
                        f"[finalize_state] 字數 {validation.word_count} 超出範圍 "
                        f"({validation.min_range}-{validation.max_range})，"
                        f"原因: {validation.rewrite_reason}。"
                        f"建議：使用 word_count_validator.build_rewrite_prompt() 進行重寫。"
                    )
                    word_count_validation_result.warnings.append(
                        f"字數超出範圍：{validation.word_count} 字，"
                        f"應在 {validation.min_range}-{validation.max_range} 字之間"
                    )

            # Phase 14 Stage 2: 先應用模板差異化（輕量驗證模式，不截斷）
            # Phase 14 Stage 3: differentiate_template 預設不截斷，只記錄警告
            if template_type in ("concise", "standard", "detailed"):
                if body_html:
                    # differentiate_template 預設不截斷（force_truncate=False）
                    processed_html = differentiate_template(body_html, template_type)
                    final_result = dict(final_result)
                    final_result["body_html"] = processed_html

            # Phase 11: 如果有 word_limit，再套用一次字數限制（覆蓋模板限制）
            # 注意：這是向後相容功能，可能添加截斷
            if word_limit:
                try:
                    from src.functions.utils.text_truncate import truncate_llm_output

                    final_result = truncate_llm_output(final_result, word_limit)
                except Exception as e:
                    logger.warning(f"Failed to apply word_limit truncation: {e}")

        except Exception as e:
            # 使用模組級別的 logger（避免函數內 local logger 遮蔽問題）
            logger.warning(f"Failed to process final result: {e}")

    # 更新狀態
    state["final_result"] = final_result
    state["current_node"] = NodeNames.END
    state["total_execution_time"] = (
        datetime.now() - state["start_time"]
    ).total_seconds()
    state["word_count_validation"] = word_count_validation_result

    return state


# ===== 狀態驗證函式 =====


def validate_state(state: CompanyBriefState) -> List[str]:
    """
    驗證狀態的完整性

    Args:
        state: 要驗證的狀態

    Returns:
        List[str]: 驗證錯誤列表，空列表表示驗證通過
    """
    errors = []

    # 檢查必要欄位
    if not state.get("organ"):
        errors.append("organ field is required")

    if not state.get("start_time"):
        errors.append("start_time field is required")

    # 檢查執行路徑
    if not isinstance(state.get("execution_path"), list):
        errors.append("execution_path must be a list")

    # 檢查重試計數
    if not isinstance(state.get("retry_counts"), dict):
        errors.append("retry_counts must be a dict")

    return errors


def is_state_complete(state: CompanyBriefState) -> bool:
    """
    檢查狀態是否完成

    Args:
        state: 要檢查的狀態

    Returns:
        bool: 狀態是否完成
    """
    return (
        state.get("current_node") == NodeNames.END
        and state.get("final_result") is not None
    )
