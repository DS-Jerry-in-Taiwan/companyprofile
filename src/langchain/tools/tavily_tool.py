# tavily_tool.py
"""
Tavily Search Tool for LangChain

將 Tavily 搜尋功能包裝為 LangChain Tool，提供標準化介面。
"""

import logging
from typing import Dict, Any, Optional
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


class TavilySearchInput(BaseModel):
    """Tavily 搜尋工具的輸入模式"""

    query: str = Field(description="搜尋查詢，例如：'台積電 官網'")
    max_results: int = Field(default=3, description="最大結果數量，預設為3")
    include_answer: bool = Field(default=True, description="是否包含 AI 生成答案")


class TavilySearchOutput(BaseModel):
    """Tavily 搜尋工具的輸出模式"""

    success: bool = Field(description="搜尋是否成功")
    answer: Optional[str] = Field(description="AI 生成的答案摘要")
    results: list = Field(description="搜尋結果列表")
    source: str = Field(description="搜尋來源（tavily、web_search、mock）")
    execution_time: float = Field(description="執行時間（秒）")
    error: Optional[str] = Field(description="錯誤訊息（如果有）")


if LANGCHAIN_TOOLS_AVAILABLE:

    class TavilySearchTool(BaseTool):
        """Tavily 搜尋工具類別"""

        name: str = "tavily_search"
        description: str = (
            "使用 Tavily API 進行網路搜尋並提取內容。"
            "適用於搜尋公司官網、產品資訊等。"
            "輸入格式：{'query': '公司名稱 官網', 'max_results': 3}"
        )
        args_schema = TavilySearchInput

        def _run(
            self,
            query: str,
            max_results: int = 3,
            include_answer: bool = True,
            run_manager: Optional[CallbackManagerForToolRun] = None,
        ) -> Dict[str, Any]:
            """執行 Tavily 搜尋"""
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

                from src.functions.utils.tavily_client import get_tavily_client
                import time

                start_time = time.time()

                # 記錄搜尋開始
                logger.info(f"[TavilyTool] 搜尋開始: {query}")

                # 執行搜尋
                tavily_client = get_tavily_client()
                result = tavily_client.search_and_extract(
                    query=query, max_results=max_results, include_answer=include_answer
                )

                execution_time = time.time() - start_time

                # 格式化輸出
                output = {
                    "success": result.get("success", False),
                    "answer": result.get("answer"),
                    "results": result.get("results", []),
                    "source": result.get("fallback_used", "tavily"),
                    "execution_time": execution_time,
                    "error": result.get("error") if not result.get("success") else None,
                }

                logger.info(
                    f"[TavilyTool] 搜尋完成: {output['success']}, 來源: {output['source']}, 耗時: {execution_time:.2f}s"
                )

                return output

            except Exception as e:
                logger.error(f"[TavilyTool] 搜尋失敗: {e}")
                return {
                    "success": False,
                    "answer": None,
                    "results": [],
                    "source": "error",
                    "execution_time": 0.0,
                    "error": str(e),
                }


# 函式版本的 Tool（更簡潔的使用方式）
@tool
def tavily_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    使用 Tavily API 進行網路搜尋並提取內容

    Args:
        query: 搜尋查詢，例如：'台積電 官網'
        max_results: 最大結果數量，預設為3

    Returns:
        包含搜尋結果的字典，包括：
        - success: 搜尋是否成功
        - answer: AI 生成的答案摘要
        - results: 搜尋結果列表
        - source: 搜尋來源
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

        from src.functions.utils.tavily_client import get_tavily_client
        import time

        start_time = time.time()

        logger.info(f"[tavily_search] 搜尋開始: {query}")

        # 執行搜尋
        tavily_client = get_tavily_client()
        result = tavily_client.search_and_extract(
            query=query, max_results=max_results, include_answer=True
        )

        execution_time = time.time() - start_time

        # 格式化輸出
        output = {
            "success": result.get("success", False),
            "answer": result.get("answer"),
            "results": result.get("results", []),
            "source": result.get("fallback_used", "tavily"),
            "execution_time": execution_time,
            "error": result.get("error") if not result.get("success") else None,
        }

        logger.info(
            f"[tavily_search] 搜尋完成: {output['success']}, 來源: {output['source']}, 耗時: {execution_time:.2f}s"
        )

        return output

    except Exception as e:
        logger.error(f"[tavily_search] 搜尋失敗: {e}")
        return {
            "success": False,
            "answer": None,
            "results": [],
            "source": "error",
            "execution_time": 0.0,
            "error": str(e),
        }


# 便捷函式
def create_tavily_search_tool():
    """建立 Tavily 搜尋工具實例"""
    if LANGCHAIN_TOOLS_AVAILABLE:
        return TavilySearchTool()
    else:
        return tavily_search


def search_company_info_tool(company_name: str) -> Dict[str, Any]:
    """
    搜尋公司資訊的便捷工具

    Args:
        company_name: 公司名稱

    Returns:
        搜尋結果字典
    """
    query = f"{company_name} 官網 公司資訊"
    return tavily_search(query, max_results=3)
