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


def generate_brief(data):
    """
    主要的公司簡介生成函式

    Args:
        data (dict): 包含以下鍵值的字典：
            - organ (str): 公司名稱
            - organNo (str, optional): 統一編號
            - companyUrl (str, optional): 公司官網
            - brief (str, optional): 用戶提供的簡介
            - word_limit (int, optional): 字數限制
            - capital (int, optional): 資本額
            - employees (int, optional): 員工人數
            - founded_year (int, optional): 成立年份
            - optimization_mode (str, optional): 模板類型 (concise/standard/detailed)

    Returns:
        dict: 生成結果，包含 title, body_html, summary 等欄位
    """
    organ = data["organ"]
    organ_no = data.get("organNo")
    user_brief = data.get("brief")
    company_url = data.get("companyUrl")
    word_limit = data.get("word_limit")
    capital = data.get("capital")
    employees = data.get("employees")
    founded_year = data.get("founded_year")
    optimization_mode = data.get("optimization_mode")  # Phase 14 Stage 2: 模板類型

    logger.info(
        f"使用 LangGraph 流程生成 {organ} 的簡介，模板類型: {optimization_mode or 'standard'}"
    )

    # 使用 LangGraph 狀態圖進行處理
    result = generate_company_brief(
        organ=organ,
        organ_no=organ_no,
        company_url=company_url,
        user_brief=user_brief,
        word_limit=word_limit,
        capital=capital,
        employees=employees,
        founded_year=founded_year,
        optimization_mode=optimization_mode,  # Phase 14 Stage 2: 傳遞模板類型
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
