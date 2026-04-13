# company_brief_graph.py
"""
公司簡介生成狀態圖

實作完整的 LangGraph 狀態圖，包括：
- 條件邊路由邏輯
- 錯誤處理分支
- 重試機制
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

logger = logging.getLogger(__name__)

from .state import (
    CompanyBriefState,
    NodeNames,
    EdgeConditions,
    NodeResult,
    NodeStatus,
    SearchResult,
    LLMResult,
    QualityCheckResult,
    ErrorInfo,
    ErrorSeverity,
    WordCountValidationResult,  # Phase 14 Stage 3 新增
    create_initial_state,
    update_state_with_node_result,
    should_retry_node,
    increment_retry_count,
    finalize_state,
)

logger = logging.getLogger(__name__)

# ===== 節點執行函式 =====


def search_node(state: CompanyBriefState) -> CompanyBriefState:
    """
    搜尋節點 - 使用配置驅動搜尋工具

    這個函式使用 ConfigDrivenSearchTool 進行公司資訊搜尋。
    實際使用的搜尋策略由 config/search_config.json 中的 provider 設定決定。

    支援的策略：
    - tavily: Tavily 批次搜尋（快速）
    - gemini_fewshot: Gemini Few-shot 搜尋（完整）
    - gemini_planner_tavily: Gemini 規劃 + Tavily 執行（彈性）

    預設策略：gemini_fewshot

    配置說明：
    - 修改 config/search_config.json 中的 provider 欄位即可切換策略
    - 動態切換：tool.switch_provider("tavily")

    與舊版差異：
    - 舊版：直接使用 tavily_client.search_and_extract()
    - 新版：使用 ConfigDrivenSearchTool.search()，由配置決定實際策略

    相關檔案：
    - src/services/config_driven_search.py: 配置驅動搜尋工具
    - config/search_config.json: 搜尋策略配置

    Args:
        state: 當前狀態，包含 organ (公司名稱) 等欄位

    Returns:
        CompanyBriefState: 更新後的狀態，search_result 包含搜尋結果
    """
    logger.info(f"執行搜尋節點，搜尋公司：{state['organ']}")
    start_time = time.time()

    try:
        # 導入搜尋功能
        import sys
        import os

        PROJECT_ROOT = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

        # 使用配置驅動搜尋工具（新）
        from src.services.config_driven_search import search as config_search

        # 執行搜尋
        search_result = config_search(f"{state['organ']} 官網")

        execution_time = time.time() - start_time

        # 建立搜尋結果（轉換為舊格式以保持向後兼容）
        result = SearchResult(
            success=search_result.success,
            answer=search_result.raw_answer,
            results=[{"data": search_result.data}],  # 將新格式的 data 包裝進 results
            source=search_result.tool_type,
            execution_time=execution_time,
            error=None if search_result.success else "搜尋失敗",
        )

        # 建立節點結果
        node_result = NodeResult(
            node_name=NodeNames.SEARCH,
            status=NodeStatus.COMPLETED if result.success else NodeStatus.FAILED,
            output=result,
            execution_time=execution_time,
        )

        if not result.success:
            node_result.error = Exception(result.error or "Search failed")

        # 更新狀態
        return update_state_with_node_result(state, node_result)

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"搜尋節點執行失敗: {e}")

        # 建立失敗結果
        result = SearchResult(
            success=False,
            error=str(e),
            execution_time=execution_time,
        )

        node_result = NodeResult(
            node_name=NodeNames.SEARCH,
            status=NodeStatus.FAILED,
            output=result,
            error=e,
            execution_time=execution_time,
        )

        return update_state_with_node_result(state, node_result)


def generate_node(state: CompanyBriefState) -> CompanyBriefState:
    """
    生成節點 - 使用 LLM 生成公司簡介

    Args:
        state: 當前狀態

    Returns:
        CompanyBriefState: 更新後的狀態
    """
    logger.info(f"執行生成節點，為 {state['organ']} 生成簡介")
    start_time = time.time()

    try:
        # 導入生成功能
        import sys
        import os

        PROJECT_ROOT = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

        from src.functions.utils.prompt_builder import build_generate_prompt
        from src.functions.utils.llm_service import call_llm

        # 準備搜尋內容
        web_content = None
        if state.get("search_result") and state["search_result"].success:
            if state["search_result"].answer:
                web_content = state["search_result"].answer
            elif state["search_result"].results:
                # 合併搜尋結果內容
                contents = []
                for result in state["search_result"].results[:3]:  # 最多取3個結果
                    if result.get("content"):
                        contents.append(result["content"])
                web_content = "\n\n".join(contents)

        # 建立 Prompt（Phase 11: 添加 word_limit, Phase 14: 添加選填欄位, Phase 14 Stage 2: 添加 optimization_mode）
        prompt = build_generate_prompt(
            organ=state["organ"],
            organ_no=state.get("organ_no"),
            company_url=state.get("company_url"),
            user_brief=state.get("user_brief"),
            web_content=web_content,
            word_limit=state.get("word_limit"),
            capital=state.get("capital"),
            employees=state.get("employees"),
            founded_year=state.get("founded_year"),
            optimization_mode=state.get(
                "optimization_mode"
            ),  # Phase 14 Stage 2: 傳遞模板類型
        )

        # 呼叫 LLM（Phase 11: 傳遞 word_limit）
        llm_response = call_llm(prompt, word_limit=state.get("word_limit"))

        execution_time = time.time() - start_time

        # 建立 LLM 結果
        result = LLMResult(
            success=True,
            title=llm_response.get("title"),
            body_html=llm_response.get("body_html"),
            summary=llm_response.get("summary"),
            execution_time=execution_time,
        )

        # 建立節點結果
        node_result = NodeResult(
            node_name=NodeNames.GENERATE,
            status=NodeStatus.COMPLETED,
            output=result,
            execution_time=execution_time,
        )

        # 更新狀態
        return update_state_with_node_result(state, node_result)

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"生成節點執行失敗: {e}")

        # 建立失敗結果
        result = LLMResult(
            success=False,
            error=str(e),
            execution_time=execution_time,
        )

        node_result = NodeResult(
            node_name=NodeNames.GENERATE,
            status=NodeStatus.FAILED,
            output=result,
            error=e,
            execution_time=execution_time,
        )

        return update_state_with_node_result(state, node_result)


def quality_check_node(state: CompanyBriefState) -> CompanyBriefState:
    """
    品質檢查節點 - 檢驗生成結果的品質
    如果品質檢查通過，也會設置最終結果

    Args:
        state: 當前狀態

    Returns:
        CompanyBriefState: 更新後的狀態
    """
    logger.info(f"執行品質檢查節點")
    start_time = time.time()

    try:
        # 取得生成結果
        llm_result = state.get("llm_result")
        if not llm_result or not llm_result.success:
            raise Exception("No valid LLM result to check")

        # 簡單的品質檢查邏輯
        issues = []
        score = 100.0

        # 檢查標題
        if not llm_result.title or len(llm_result.title.strip()) < 5:
            issues.append({"type": "title", "message": "標題過短或為空"})
            score -= 20

        # 檢查內容
        if not llm_result.body_html or len(llm_result.body_html.strip()) < 100:
            issues.append({"type": "content", "message": "內容過短"})
            score -= 30

        # 檢查摘要
        if not llm_result.summary or len(llm_result.summary.strip()) < 20:
            issues.append({"type": "summary", "message": "摘要過短或為空"})
            score -= 20

        # 檢查是否包含公司名稱
        company_name = state["organ"]
        has_company_name = (
            (llm_result.title and company_name in llm_result.title)
            or (llm_result.body_html and company_name in llm_result.body_html)
            or (llm_result.summary and company_name in llm_result.summary)
        )

        if not has_company_name:
            issues.append({"type": "company_name", "message": "結果中未包含公司名稱"})
            score -= 30

        execution_time = time.time() - start_time
        passed = score >= 70.0  # 70分以上算通過

        # 建立品質檢查結果
        result = QualityCheckResult(
            passed=passed,
            score=score,
            issues=issues,
            suggestions=[],  # 可以在這裡添加改善建議
            details={
                "title_length": len(llm_result.title or ""),
                "content_length": len(llm_result.body_html or ""),
                "summary_length": len(llm_result.summary or ""),
                "has_company_name": has_company_name,
            },
        )

        # 如果品質檢查通過，直接設置最終結果
        if passed:
            search_result = state.get("search_result")
            final_result = {
                "title": llm_result.title,
                "body_html": llm_result.body_html,
                "summary": llm_result.summary,
                "quality_score": score,
                "search_source": search_result.source if search_result else "unknown",
            }
            state["final_result"] = final_result

        # 建立節點結果
        node_result = NodeResult(
            node_name=NodeNames.QUALITY_CHECK,
            status=NodeStatus.COMPLETED,
            output=result,
            execution_time=execution_time,
        )

        # 更新狀態
        return update_state_with_node_result(state, node_result)

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"品質檢查節點執行失敗: {e}")

        # 建立失敗結果
        result = QualityCheckResult(
            passed=False,
            score=0.0,
            issues=[{"type": "error", "message": str(e)}],
        )

        node_result = NodeResult(
            node_name=NodeNames.QUALITY_CHECK,
            status=NodeStatus.FAILED,
            output=result,
            error=e,
            execution_time=execution_time,
        )

        return update_state_with_node_result(state, node_result)


def error_handler_node(state: CompanyBriefState) -> CompanyBriefState:
    """
    錯誤處理節點 - 處理無法恢復的錯誤

    Args:
        state: 當前狀態

    Returns:
        CompanyBriefState: 更新後的狀態
    """
    logger.info("執行錯誤處理節點")

    # 建立預設結果
    company_name = state["organ"]
    default_result = {
        "title": f"{company_name} - 企業簡介",
        "body_html": f"<p>{company_name} 是一家專業的企業，致力於提供優質的產品和服務。由於技術問題，無法取得更詳細的資訊，請聯繫我們獲取最新資料。</p>",
        "summary": f"{company_name} - 專業企業，提供優質產品和服務。",
        "error_handled": True,
        "errors": [error.error_message for error in state["errors"]],
    }

    # 設置最終結果
    state["final_result"] = default_result

    return state


# ===== 路由決策函式 =====


def route_after_search(state: CompanyBriefState) -> str:
    """
    搜尋後的路由決策

    Args:
        state: 當前狀態

    Returns:
        str: 下一個節點名稱
    """
    search_result = state.get("search_result")

    if not search_result:
        return NodeNames.ERROR_HANDLER

    if search_result.success:
        logger.info("搜尋成功，進入生成階段")
        return NodeNames.GENERATE
    else:
        # 搜尋失敗，檢查是否可以重試
        if should_retry_node(state, NodeNames.SEARCH):
            logger.info("搜尋失敗，嘗試重試")
            return NodeNames.RETRY_SEARCH
        else:
            logger.warning("搜尋失敗且無法重試，使用錯誤處理")
            return NodeNames.ERROR_HANDLER


def route_after_generate(state: CompanyBriefState) -> str:
    """
    生成後的路由決策

    Args:
        state: 當前狀態

    Returns:
        str: 下一個節點名稱
    """
    llm_result = state.get("llm_result")

    if not llm_result:
        return NodeNames.ERROR_HANDLER

    if llm_result.success:
        logger.info("生成成功，進入品質檢查")
        return NodeNames.QUALITY_CHECK
    else:
        # 生成失敗，檢查是否可以重試
        if should_retry_node(state, NodeNames.GENERATE):
            logger.info("生成失敗，嘗試重試")
            return NodeNames.RETRY_GENERATE
        else:
            logger.warning("生成失敗且無法重試，使用錯誤處理")
            return NodeNames.ERROR_HANDLER


def route_after_quality_check(state: CompanyBriefState) -> str:
    """
    品質檢查後的路由決策

    Args:
        state: 當前狀態

    Returns:
        str: 下一個節點名稱或 END
    """
    quality_result = state.get("quality_check_result")

    if not quality_result:
        return NodeNames.ERROR_HANDLER

    if quality_result.passed:
        logger.info("品質檢查通過，完成流程")
        return END
    else:
        # 品質檢查失敗，檢查是否可以重試生成
        if should_retry_node(state, NodeNames.GENERATE):
            logger.info("品質檢查失敗，重新生成")
            return NodeNames.RETRY_GENERATE
        else:
            logger.warning("品質檢查失敗且無法重試，進入錯誤處理")
            return NodeNames.ERROR_HANDLER


def retry_search_node(state: CompanyBriefState) -> CompanyBriefState:
    """
    重試搜尋節點

    Args:
        state: 當前狀態

    Returns:
        CompanyBriefState: 更新後的狀態
    """
    # 增加重試計數
    state = increment_retry_count(state, NodeNames.SEARCH)
    logger.info(f"重試搜尋，第 {state['retry_counts'][NodeNames.SEARCH]} 次")

    # 執行搜尋邏輯
    return search_node(state)


def retry_generate_node(state: CompanyBriefState) -> CompanyBriefState:
    """
    重試生成節點

    Args:
        state: 當前狀態

    Returns:
        CompanyBriefState: 更新後的狀態
    """
    # 增加重試計數
    state = increment_retry_count(state, NodeNames.GENERATE)
    logger.info(f"重試生成，第 {state['retry_counts'][NodeNames.GENERATE]} 次")

    # 執行生成邏輯
    return generate_node(state)


# ===== 狀態圖建構器 =====


class CompanyBriefGraph:
    """公司簡介生成狀態圖"""

    def __init__(self):
        """初始化狀態圖"""
        self.graph = None
        self.compiled_graph = None
        self._build_graph()

    def _build_graph(self):
        """建構狀態圖"""
        # 建立狀態圖
        self.graph = StateGraph(CompanyBriefState)

        # 添加節點
        self.graph.add_node(NodeNames.SEARCH, search_node)
        self.graph.add_node(NodeNames.GENERATE, generate_node)
        self.graph.add_node(NodeNames.QUALITY_CHECK, quality_check_node)
        self.graph.add_node(NodeNames.ERROR_HANDLER, error_handler_node)
        self.graph.add_node(NodeNames.RETRY_SEARCH, retry_search_node)
        self.graph.add_node(NodeNames.RETRY_GENERATE, retry_generate_node)

        # 設定入口點
        self.graph.set_entry_point(NodeNames.SEARCH)

        # 添加條件邊
        self.graph.add_conditional_edges(
            NodeNames.SEARCH,
            route_after_search,
            {
                NodeNames.GENERATE: NodeNames.GENERATE,
                NodeNames.RETRY_SEARCH: NodeNames.RETRY_SEARCH,
                NodeNames.ERROR_HANDLER: NodeNames.ERROR_HANDLER,
            },
        )

        self.graph.add_conditional_edges(
            NodeNames.GENERATE,
            route_after_generate,
            {
                NodeNames.QUALITY_CHECK: NodeNames.QUALITY_CHECK,
                NodeNames.RETRY_GENERATE: NodeNames.RETRY_GENERATE,
                NodeNames.ERROR_HANDLER: NodeNames.ERROR_HANDLER,
            },
        )

        self.graph.add_conditional_edges(
            NodeNames.QUALITY_CHECK,
            route_after_quality_check,
            {
                END: END,
                NodeNames.RETRY_GENERATE: NodeNames.RETRY_GENERATE,
                NodeNames.ERROR_HANDLER: NodeNames.ERROR_HANDLER,
            },
        )

        self.graph.add_conditional_edges(
            NodeNames.RETRY_SEARCH,
            route_after_search,
            {
                NodeNames.GENERATE: NodeNames.GENERATE,
                NodeNames.RETRY_SEARCH: NodeNames.RETRY_SEARCH,
                NodeNames.ERROR_HANDLER: NodeNames.ERROR_HANDLER,
            },
        )

        self.graph.add_conditional_edges(
            NodeNames.RETRY_GENERATE,
            route_after_generate,
            {
                NodeNames.QUALITY_CHECK: NodeNames.QUALITY_CHECK,
                NodeNames.RETRY_GENERATE: NodeNames.RETRY_GENERATE,
                NodeNames.ERROR_HANDLER: NodeNames.ERROR_HANDLER,
            },
        )

        # 錯誤處理節點直接結束
        self.graph.add_edge(NodeNames.ERROR_HANDLER, END)

        # 編譯圖
        self.compiled_graph = self.graph.compile()

    def invoke(
        self,
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
    ) -> Dict[str, Any]:
        """
        執行公司簡介生成流程

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
            Dict[str, Any]: 最終結果
        """
        logger.info(f"開始生成 {organ} 的公司簡介")

        # 建立初始狀態（Phase 11: 添加 word_limit, Phase 14: 添加選填欄位, Phase 14 Stage 2: 添加 optimization_mode）
        initial_state = create_initial_state(
            organ,
            organ_no,
            company_url,
            user_brief,
            word_limit,
            capital,
            employees,
            founded_year,
            optimization_mode,
            max_rewrite_attempts,
        )

        # 使用 LangGraph 執行
        final_state = self.compiled_graph.invoke(initial_state)

        # Phase 14 Stage 2: 在回傳前呼叫 finalize_state
        # 套用 differentiate_template 模板差異化截斷
        # Phase 14 Stage 3: 同時整合字數檢核
        final_result = final_state.get("final_result", {})
        if final_result:
            final_state = finalize_state(final_state, final_result)
            final_result = final_state.get("final_result", {})

        return final_result


# ===== 公用介面 =====


def create_company_brief_graph() -> CompanyBriefGraph:
    """建立公司簡介生成圖實例"""
    return CompanyBriefGraph()


def generate_company_brief(
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
) -> Dict[str, Any]:
    """
    生成公司簡介的便捷函式

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
        Dict[str, Any]: 生成結果
    """
    graph = create_company_brief_graph()
    return graph.invoke(
        organ,
        organ_no,
        company_url,
        user_brief,
        word_limit,
        capital,
        employees,
        founded_year,
        optimization_mode,
        max_rewrite_attempts,
    )
