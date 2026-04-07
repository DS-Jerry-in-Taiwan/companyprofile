# search_tool.py
"""
Web Search Tool for LangChain

將傳統的 web_search 功能包裝為 LangChain Tool。
作為 Tavily 的備用搜尋方案。
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

try:
    from langchain.tools import tool, BaseTool
    from langchain.callbacks.manager import CallbackManagerForToolRun

    LANGCHAIN_TOOLS_AVAILABLE = True
except ImportError:
    # 如果 LangChain tools 還未安裝，提供基本實作
    BaseTool = object
    tool = lambda func: func
    CallbackManagerForToolRun = object
    BaseModel = object
    Field = lambda **kwargs: None
    LANGCHAIN_TOOLS_AVAILABLE = False

logger = logging.getLogger(__name__)


class WebSearchInput(BaseModel):
    """Web Search 工具的輸入模式"""

    company_name: str = Field(description="公司名稱，例如：'台積電'")
    company_url: Optional[str] = Field(default=None, description="公司官網（可選）")


class WebSearchOutput(BaseModel):
    """Web Search 工具的輸出模式"""

    success: bool = Field(description="搜尋是否成功")
    urls: List[str] = Field(description="找到的 URL 列表")
    execution_time: float = Field(description="執行時間（秒）")
    error: Optional[str] = Field(description="錯誤訊息（如果有）")


if LANGCHAIN_TOOLS_AVAILABLE:

    class WebSearchTool(BaseTool):
        """Web Search 工具類別"""

        name: str = "web_search"
        description: str = (
            "使用傳統網路搜尋方式查找公司官網。"
            "適用於作為 Tavily 的備用搜尋方案。"
            "輸入格式：{'company_name': '公司名稱', 'company_url': '可選官網'}"
        )
        args_schema = WebSearchInput

        def _run(
            self,
            company_name: str,
            company_url: Optional[str] = None,
            run_manager: Optional[CallbackManagerForToolRun] = None,
        ) -> Dict[str, Any]:
            """執行 Web 搜尋"""
            try:
                # 導入搜尋功能
                import sys
                import os

                PROJECT_ROOT = os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        )
                    )
                )
                if PROJECT_ROOT not in sys.path:
                    sys.path.insert(0, PROJECT_ROOT)

                from src.functions.utils.web_search import web_search
                import time

                start_time = time.time()

                # 記錄搜尋開始
                logger.info(f"[WebSearchTool] 搜尋開始: {company_name}")

                # 執行搜尋
                urls = web_search(company_name, company_url)

                execution_time = time.time() - start_time

                # 格式化輸出
                output = {
                    "success": bool(urls),
                    "urls": urls or [],
                    "execution_time": execution_time,
                    "error": None if urls else "No URLs found",
                }

                logger.info(
                    f"[WebSearchTool] 搜尋完成: {output['success']}, 找到 {len(output['urls'])} 個URL, 耗時: {execution_time:.2f}s"
                )

                return output

            except Exception as e:
                logger.error(f"[WebSearchTool] 搜尋失敗: {e}")
                return {
                    "success": False,
                    "urls": [],
                    "execution_time": 0.0,
                    "error": str(e),
                }


# 函式版本的 Tool
@tool
def web_search_tool(
    company_name: str, company_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    使用傳統網路搜尋查找公司官網

    Args:
        company_name: 公司名稱，例如：'台積電'
        company_url: 公司官網（可選，如果提供會優先使用）

    Returns:
        包含搜尋結果的字典：
        - success: 搜尋是否成功
        - urls: 找到的 URL 列表
        - execution_time: 執行時間
    """
    try:
        # 導入搜尋功能
        import sys
        import os

        PROJECT_ROOT = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
        )
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

        from src.functions.utils.web_search import web_search
        import time

        start_time = time.time()

        logger.info(f"[web_search_tool] 搜尋開始: {company_name}")

        # 執行搜尋
        urls = web_search(company_name, company_url)

        execution_time = time.time() - start_time

        # 格式化輸出
        output = {
            "success": bool(urls),
            "urls": urls or [],
            "execution_time": execution_time,
            "error": None if urls else "No URLs found",
        }

        logger.info(
            f"[web_search_tool] 搜尋完成: {output['success']}, 找到 {len(output['urls'])} 個URL, 耗時: {execution_time:.2f}s"
        )

        return output

    except Exception as e:
        logger.error(f"[web_search_tool] 搜尋失敗: {e}")
        return {
            "success": False,
            "urls": [],
            "execution_time": 0.0,
            "error": str(e),
        }


@tool
def extract_content_tool(urls: List[str]) -> Dict[str, Any]:
    """
    從 URL 列表提取內容

    Args:
        urls: URL 列表

    Returns:
        包含提取結果的字典：
        - success: 是否成功
        - contents: 提取的內容列表
        - execution_time: 執行時間
    """
    try:
        # 導入內容提取功能
        import sys
        import os

        PROJECT_ROOT = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            )
        )
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

        from src.functions.utils.web_scraper import extract_main_content
        import time

        start_time = time.time()

        logger.info(f"[extract_content_tool] 開始提取 {len(urls)} 個URL的內容")

        contents = []
        for url in urls[:3]:  # 最多處理3個URL
            try:
                content = extract_main_content(url)
                if content:
                    contents.append(
                        {
                            "url": url,
                            "content": content,
                            "success": True,
                        }
                    )
                else:
                    contents.append(
                        {
                            "url": url,
                            "content": "",
                            "success": False,
                            "error": "Empty content",
                        }
                    )
            except Exception as e:
                contents.append(
                    {
                        "url": url,
                        "content": "",
                        "success": False,
                        "error": str(e),
                    }
                )

        execution_time = time.time() - start_time
        successful_extractions = sum(1 for c in contents if c["success"])

        output = {
            "success": successful_extractions > 0,
            "contents": contents,
            "successful_count": successful_extractions,
            "total_count": len(contents),
            "execution_time": execution_time,
            "error": None if successful_extractions > 0 else "No content extracted",
        }

        logger.info(
            f"[extract_content_tool] 提取完成: 成功 {successful_extractions}/{len(contents)}, 耗時: {execution_time:.2f}s"
        )

        return output

    except Exception as e:
        logger.error(f"[extract_content_tool] 提取失敗: {e}")
        return {
            "success": False,
            "contents": [],
            "successful_count": 0,
            "total_count": 0,
            "execution_time": 0.0,
            "error": str(e),
        }


# 便捷函式
def create_web_search_tool():
    """建立 Web Search 工具實例"""
    if LANGCHAIN_TOOLS_AVAILABLE:
        return WebSearchTool()
    else:
        return web_search_tool


def search_and_extract_company_info(
    company_name: str, company_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    搜尋並提取公司資訊的便捷工具

    Args:
        company_name: 公司名稱
        company_url: 公司官網（可選）

    Returns:
        包含搜尋和提取結果的字典
    """
    # 第一步：搜尋URL
    search_result = web_search_tool(company_name, company_url)

    if not search_result["success"] or not search_result["urls"]:
        return {
            "success": False,
            "search_result": search_result,
            "extraction_result": None,
            "error": "Web search failed or no URLs found",
        }

    # 第二步：提取內容
    extraction_result = extract_content_tool(search_result["urls"])

    return {
        "success": extraction_result["success"],
        "search_result": search_result,
        "extraction_result": extraction_result,
        "error": extraction_result.get("error"),
    }
