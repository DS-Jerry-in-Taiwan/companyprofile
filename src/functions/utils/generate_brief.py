# generate_brief.py
"""
Generate Brief Module - LangGraph 統一流程
- 使用 LangGraph 狀態圖進行流程控制
- 提供 Few-shot 範例提升資訊使用率
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

# 確保 src 目錄在 Python 路徑中
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 導入 LangGraph 狀態圖
try:
    from src.langgraph_state.company_brief_graph import (
        generate_company_brief,
        create_company_brief_graph,
    )

    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    raise ImportError(
        f"LangGraph 模組不可用，無法執行生成服務: {e}\n"
        "請確認 langgraph 相關依賴已正確安裝。"
    )

from src.functions.utils.error_handler import ExternalServiceError, LLMServiceError


def generate_brief(data):
    """
    生成公司簡介

    Args:
        data: dict，包含以下欄位
            - organ (str): 公司名稱（必需）
            - organNo (str, optional): 統一編號
            - companyUrl (str, optional): 公司官網
            - inputText (str, optional): 用戶提供的簡介素材
            - capital (int, optional): 資本額
            - employees (int, optional): 員工人數
            - founded_year (int, optional): 成立年份
            - optimization_mode (str, optional): 模板類型 (concise/standard/detailed)

    Returns:
        dict: 生成結果，包含 title, body_html, summary 等欄位
    """
    organ = data["organ"]
    organ_no = data.get("organNo")
    company_url = data.get("companyUrl")
    input_text = data.get("inputText") or data.get("brief")
    capital = data.get("capital")
    employees = data.get("employees")
    founded_year = data.get("founded_year")
    optimization_mode = data.get("optimization_mode")  # Phase 14 Stage 2: 模板類型

    # 彙整 user_input dict（把所有前端欄位存進 DB）
    user_input = {}
    
    # 公司官網
    if company_url:
        user_input["company_url"] = company_url
    
    # 文字欄位
    if data.get("brand_names"):
        user_input["brand_names"] = data["brand_names"]
    if data.get("tax_id"):
        user_input["tax_id"] = data["tax_id"]
    if data.get("address"):
        user_input["address"] = data["address"]
    if data.get("industry"):
        user_input["industry"] = data["industry"]
    if data.get("industry_desc"):
        user_input["industry_desc"] = data["industry_desc"]
    
    # 數值欄位（格式化）
    if capital and capital > 0:
        user_input["capital"] = f"{capital} 萬元"
    if founded_year:
        user_input["founded_year"] = f"{founded_year} 年"
    if employees:
        user_input["employees"] = f"{employees} 人"
    
    # 現有簡介
    if input_text:
        user_input["user_brief"] = input_text

    logger.info(
        f"使用 LangGraph 流程生成 {organ} 的簡介，模板類型: {optimization_mode or 'standard'}"
    )

    try:
        # 使用 LangGraph 狀態圖進行處理
        # 傳入 user_input dict（規格化 input）
        result = generate_company_brief(
            organ=organ,
            organ_no=organ_no,
            company_url=company_url,
            user_input=user_input,  # {} 也傳，不要轉 None
            optimization_mode=optimization_mode,
        )
    except ExternalServiceError as e:
        from src.functions.utils.error_handler import LLMServiceError
        raise LLMServiceError(
            code=e.code,
            message=e.message,
            recoverable=e.recoverable
        )
    except Exception as e:
        from src.functions.utils.error_handler import LLMServiceError, ErrorCode
        # 嘗試取用原始異常的 code/message（如果有定義的話）
        code = getattr(e, 'code', None) or ErrorCode.SVC_001.code
        message = getattr(e, 'message', None) or f"{type(e).__name__}: {str(e)}"
        recoverable = getattr(e, 'recoverable', True)
        raise LLMServiceError(
            code=code,
            message=message,
            recoverable=recoverable,
        )

    # 確保回傳格式與原有 API 一致
    return {
        "title": result.get("title", f"{organ} - 企業簡介"),
        "body_html": result.get("body_html", f"<p>{organ} 的企業資訊。</p>"),
        "summary": result.get("summary", f"{organ} 企業資訊"),
        "quality_score": result.get("quality_score"),
        "search_source": result.get("search_source"),
        "quality_warning": result.get("quality_warning", False),
        "error_handled": result.get("error_handled", False),
        "processing_mode": "langgraph",
    }
