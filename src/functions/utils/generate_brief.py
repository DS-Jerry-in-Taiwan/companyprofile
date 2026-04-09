# generate_brief.py
"""
Generate Brief Module - Phase 9 LangChain/LangGraph Integration
- 整合 LangGraph 狀態圖進行統一流程控制
- 支援動態路由、錯誤處理和重試機制
- 相容原有 API 介面，可選使用 LangGraph 或傳統流程
"""

import logging
import os
import sys
from utils.web_search import web_search

logger = logging.getLogger(__name__)

# 確保 src 目錄在 Python 路徑中
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 嘗試導入 LangGraph 狀態圖
try:
    from src.langgraph.company_brief_graph import (
        generate_company_brief,
        create_company_brief_graph,
    )

    LANGGRAPH_AVAILABLE = True
    logger.info("LangGraph 狀態圖可用，將使用新的統一流程")
except ImportError as e:
    logger.warning(f"LangGraph 狀態圖不可用，使用傳統流程: {e}")
    LANGGRAPH_AVAILABLE = False

    # 建立 dummy 函式避免 unbound 錯誤
    def generate_company_brief(*args, **kwargs):
        raise NotImplementedError("LangGraph not available")


# 嘗試導入 LangChain 錯誤處理（用於傳統流程）
try:
    from src.langchain.error_handlers import RunnableWithRetryAndFallbacks
    from src.langchain.retry_config import get_retry_config, get_fallback_config

    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain error handling not available: {e}")
    LANGCHAIN_AVAILABLE = False

# 傳統流程依賴（當 LangGraph 不可用時）
from utils.tavily_client import TavilyClient, get_tavily_client
from utils.text_preprocessor import preprocess_text
from utils.prompt_builder import build_generate_prompt
from utils.llm_service import call_llm
from utils.post_processing import post_process
from utils.error_handler import ExternalServiceError
from utils.text_truncate import truncate_llm_output


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

    Returns:
        dict: 生成結果，包含 title, body_html, summary 等欄位
    """
    organ = data["organ"]
    # 取出用戶提供的素材
    organ_no = data.get("organNo")
    user_brief = data.get("brief")
    company_url = data.get("companyUrl")
    word_limit = data.get("word_limit")
    # Phase 14: 取出選填欄位
    capital = data.get("capital")
    employees = data.get("employees")
    founded_year = data.get("founded_year")

    # Phase 9: 優先使用 LangGraph 狀態圖處理
    if LANGGRAPH_AVAILABLE:
        logger.info(f"使用 LangGraph 狀態圖生成 {organ} 的簡介")
        try:
            # 使用 LangGraph 狀態圖進行統一處理（Phase 11: 添加 word_limit, Phase 14: 添加選填欄位）
            result = generate_company_brief(
                organ=organ,
                organ_no=organ_no,
                company_url=company_url,
                user_brief=user_brief,
                word_limit=word_limit,
                capital=capital,
                employees=employees,
                founded_year=founded_year,
            )

            # 確保回傳格式與原有 API 一致
            return {
                "title": result.get("title", f"{organ} - 企業簡介"),
                "body_html": result.get("body_html", f"<p>{organ} 的企業資訊。</p>"),
                "summary": result.get("summary", f"{organ} 企業資訊"),
                # 新增的品質和來源資訊
                "quality_score": result.get("quality_score"),
                "search_source": result.get("search_source"),
                "quality_warning": result.get("quality_warning", False),
                "error_handled": result.get("error_handled", False),
                "processing_mode": "langgraph",
            }
        except Exception as e:
            logger.error(f"LangGraph 狀態圖執行失敗，回退到傳統流程: {e}")
            # 發生錯誤時回退到傳統流程

    # 傳統流程（當 LangGraph 不可用或失敗時）
    logger.info(f"使用傳統流程生成 {organ} 的簡介")
    return _generate_brief_traditional(data)


def _generate_brief_traditional(data):
    """
    傳統的公司簡介生成流程（Phase 8 實作）
    當 LangGraph 不可用或失敗時使用

    Args:
        data (dict): 輸入資料

    Returns:
        dict: 生成結果
    """
    organ = data["organ"]
    organ_no = data.get("organNo")
    user_brief = data.get("brief")
    company_url = data.get("companyUrl")
    word_limit = data.get("word_limit")
    # Phase 14: 取出選填欄位
    capital = data.get("capital")
    employees = data.get("employees")
    founded_year = data.get("founded_year")

    # Step 1: 使用 Tavily 一次搞定搜尋和內容提取
    try:
        tavily_client = get_tavily_client()

        # 使用 Tavily 的 get_search_info 一次取得搜尋結果和內容
        search_result = tavily_client.search_and_extract(
            query=f"{organ} 官網", max_results=3
        )

        # 檢查是否成功
        if not search_result.get("success"):
            # Tavily 失敗時fallback 到舊的 web_search
            logger.warning(
                "Tavily search failed, falling back to traditional web search"
            )
            url_candidates = web_search(organ, company_url)

            if not url_candidates and not company_url:
                raise ExternalServiceError(
                    "No company URL available. Please provide a companyUrl or ensure the organ name yields search results."
                )

            # 使用傳統方式提取內容
            from .web_scraper import extract_main_content

            target_url = url_candidates[0] if url_candidates else company_url
            raw_content = extract_main_content(target_url)
        else:
            # Tavily 成功取得結果
            results = search_result.get("results", [])
            if not results:
                raise ExternalServiceError(
                    "No search results found. Please provide a companyUrl."
                )

            # 合併 Tavily 取得的內容
            # 我們可以選擇使用 answer 或個別結果的 content
            answer = search_result.get("answer")
            if answer:
                # 使用 Tavily 的 AI 生成答案作為主要內容
                raw_content = answer
            else:
                # 使用第一個結果的 content
                raw_content = results[0].get("content", "") if results else ""

            if not raw_content:
                # 如果沒有內容，fallback 到 URL 列表
                url_candidates = [r.get("url") for r in results if r.get("url")]
                if url_candidates:
                    from .web_scraper import extract_main_content

                    target_url = url_candidates[0]
                    raw_content = extract_main_content(target_url)
                else:
                    raise ExternalServiceError(
                        "Failed to extract company content from any source."
                    )

    except ExternalServiceError:
        raise
    except Exception as exc:
        raise ExternalServiceError(
            f"Failed to fetch company content: {str(exc)}"
        ) from exc

    # 2. 前處理
    clean_text = preprocess_text(raw_content)
    # 3. Prompt 組裝（傳遞所有素材，包括 Phase 14 選填欄位）
    prompt = build_generate_prompt(
        organ=organ,
        organ_no=organ_no,
        company_url=company_url,
        user_brief=user_brief,
        web_content=clean_text,
        word_limit=word_limit,
        capital=capital,
        employees=employees,
        founded_year=founded_year,
    )
    # 4. 呼叫 LLM（Phase 11: 傳遞 word_limit）
    llm_result = call_llm(prompt, word_limit=word_limit)
    # 5. 後處理並添加處理模式標識
    result = post_process(llm_result)

    # 6. 字數截斷（Phase 11 新增）
    if word_limit:
        result = truncate_llm_output(result, word_limit)

    result["processing_mode"] = "traditional"
    return result
