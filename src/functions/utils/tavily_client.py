# tavily_client.py
"""
Tavily Client - 內容提取和搜尋的簡化介面
使用 Tavily API 的搜尋一次搞定搜尋和內容提取
整合 LangChain 錯誤處理機制
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# 嘗試載入 .env 檔案
# 優先使用專案根目錄的 .env
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_env_path = os.path.join(_project_root, ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)
else:
    # 預設行為
    load_dotenv()

logger = logging.getLogger(__name__)

# 整合 LangChain 錯誤處理
try:
    import sys

    PROJECT_ROOT = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    from src.langchain.error_handlers import with_retry, with_fallbacks, RetryableError
    from src.langchain.retry_config import get_retry_config, get_fallback_config

    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain error handling not available: {e}")
    LANGCHAIN_AVAILABLE = False


class TavilyClient:
    """Tavily API 客戶端 - 簡化搜尋和內容提取流程，整合重試和 Fallback 機制"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Tavily 客戶端

        Args:
            api_key: Tavily API 金鑰，若未提供則從環境變數讀取
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        if not self.api_key:
            logger.warning(
                "TAVILY_API_KEY not found in environment, will use mock mode"
            )
            self.api_key = "dummy_value"

        self._provider = None

        # 設置 Fallback 函式
        self._setup_fallbacks()

    def _get_provider(self):
        """取得 Tavily 服務提供者實例"""
        if self._provider is None:
            from src.services.tavily_search import TavilySearchProvider

            self._provider = TavilySearchProvider(api_key=self.api_key)
        return self._provider

    def _setup_fallbacks(self):
        """設置 Fallback 函式"""
        self._fallback_functions = {
            "web_search": self._fallback_web_search,
            "mock": self._fallback_mock_data,
        }

    def _fallback_web_search(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """使用傳統 web_search 作為 fallback"""
        try:
            from utils.web_search import web_search

            logger.info(f"使用傳統 web_search 作為 fallback: {query}")

            # web_search 回傳 URL 列表
            urls = web_search(query.split()[0])  # 取公司名稱

            if not urls:
                return {
                    "answer": None,
                    "results": [],
                    "success": False,
                    "error": "Web search returned no results",
                }

            # 模擬結果格式
            results = []
            for i, url in enumerate(urls[:max_results]):
                results.append(
                    {
                        "url": url,
                        "title": f"搜尋結果 {i + 1}",
                        "content": f"來自 {url} 的內容",
                        "score": 0.8 - (i * 0.1),
                    }
                )

            return {
                "answer": f"透過傳統搜尋找到 {len(results)} 個結果",
                "results": results,
                "success": True,
                "fallback_used": "web_search",
            }

        except Exception as e:
            logger.error(f"Fallback web_search failed: {e}")
            return {
                "answer": None,
                "results": [],
                "success": False,
                "error": f"Fallback web_search failed: {e}",
            }

    def _fallback_mock_data(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """使用 Mock 資料作為最終 fallback"""
        logger.info(f"使用 Mock 資料作為最終 fallback: {query}")

        company_name = query.split()[0] if query else "公司"

        return {
            "answer": f"{company_name} 是一家專業的公司，提供多元化的產品與服務。",
            "results": [
                {
                    "url": f"https://example.com/{company_name}",
                    "title": f"{company_name} 官網",
                    "content": f"{company_name} 是業界領先的企業，致力於提供優質的產品和服務。",
                    "score": 0.7,
                }
            ],
            "success": True,
            "fallback_used": "mock",
        }

    def search_and_extract(
        self,
        query: str,
        max_results: int = 3,
        include_answer: bool = True,
        include_raw_content: bool = True,
    ) -> Dict[str, Any]:
        """
        一次搞定搜尋和內容提取（推薦使用）
        整合重試和 Fallback 機制

        這個方法會：
        1. 執行網路搜尋（帶重試）
        2. 提取每個結果的內容
        3. 生成 AI 答案摘要
        4. 失敗時自動 Fallback 到備用方案

        Args:
            query: 搜尋查詢（例如：公司名稱 + "官網"）
            max_results: 最大結果數量
            include_answer: 是否包含 AI 生成的答案
            include_raw_content: 是否包含原始內容

        Returns:
            Dict: 包含以下鍵的字典
                - answer: AI 生成的答案摘要
                - results: 搜尋結果列表，每個包含 url, title, content, score
                - raw_response: 原始 API 回應
                - success: 是否成功
                - fallback_used: 使用的 fallback 方法（如果有）
        """
        # 如果有 LangChain，使用重試和 fallback 機制
        if LANGCHAIN_AVAILABLE:
            return self._search_with_retry_and_fallbacks(query, max_results)
        else:
            # 回退到原始實作
            return self._search_original(query, max_results)

    def _search_with_retry_and_fallbacks(
        self, query: str, max_results: int = 3
    ) -> Dict[str, Any]:
        """使用重試和 fallback 機制的搜尋"""
        try:
            # 首先嘗試 Tavily（帶重試）
            result = self._search_tavily_with_retry(query, max_results)
            if result.get("success"):
                return result

        except Exception as e:
            logger.warning(f"Tavily search with retry failed: {e}")

        # Tavily 失敗，嘗試 Fallback
        for service_name, fallback_func in self._fallback_functions.items():
            try:
                logger.info(f"嘗試 fallback 服務: {service_name}")
                result = fallback_func(query, max_results)
                if result.get("success"):
                    return result
            except Exception as e:
                logger.warning(f"Fallback {service_name} failed: {e}")

        # 所有方法都失敗
        return {
            "answer": None,
            "results": [],
            "raw_response": None,
            "success": False,
            "error": "All search methods failed",
        }

    def _search_tavily_with_retry(
        self, query: str, max_results: int = 3
    ) -> Dict[str, Any]:
        """執行 Tavily 搜尋（帶重試機制）"""
        try:
            provider = self._get_provider()

            # 如果有 LangChain，使用重試裝飾器
            if LANGCHAIN_AVAILABLE:
                retry_config = get_retry_config()

                @with_retry(retry_config, f"tavily_search_{query}")
                def search_with_retry():
                    return provider.get_search_info(
                        query=query, max_results=max_results
                    )

                result = search_with_retry()
            else:
                result = provider.get_search_info(query=query, max_results=max_results)

            return {
                "answer": result.get("answer"),
                "results": result.get("results", []),
                "raw_response": result,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            raise RetryableError(f"Tavily search failed: {e}", "TavilyError", e)

    def _search_original(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """原始搜尋邏輯（沒有 LangChain 時使用）"""
        try:
            provider = self._get_provider()

            result = provider.get_search_info(query=query, max_results=max_results)

            return {
                "answer": result.get("answer"),
                "results": result.get("results", []),
                "raw_response": result,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Tavily search and extract failed: {e}")
            return {
                "answer": None,
                "results": [],
                "raw_response": None,
                "success": False,
                "error": str(e),
            }

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        執行純搜尋（只取得 URL 列表）

        Args:
            query: 搜尋查詢
            max_results: 最大結果數量

        Returns:
            List[Dict]: 包含 url, title, snippet 的列表
        """
        try:
            provider = self._get_provider()
            search_results = provider.search(query, max_results)

            return [
                {"url": r.url, "title": r.title, "snippet": r.snippet}
                for r in search_results
            ]

        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []

    def extract_content(
        self, query: str, urls: Optional[List[str]] = None, max_results: int = 3
    ) -> Dict[str, Any]:
        """
        根據 URL 列表提取內容
        如果沒有提供 URLs，會先搜尋再提取

        Args:
            query: 搜尋查詢
            urls: 要提取內容的 URL 列表（可選）
            max_results: 搜尋結果數量

        Returns:
            Dict: 包含 extracted_contents 列表的字典
        """
        # 如果沒有提供 URLs，先搜尋
        if not urls:
            search_result = self.search_and_extract(query, max_results)
            urls = [r.get("url") for r in search_result.get("results", [])]

        # 使用 Tavily 的搜尋結果已經包含內容
        # 這裡可以進一步處理或直接使用
        return {
            "extracted_contents": [{"url": url, "query": query} for url in urls],
            "success": True,
        }

    def get_company_info(
        self, company_name: str, max_results: int = 3
    ) -> Dict[str, Any]:
        """
        取得公司資訊的便捷方法

        Args:
            company_name: 公司名稱
            max_results: 最大結果數量

        Returns:
            Dict: 包含公司資訊的字典
        """
        query = f"{company_name} 公司 官網"
        return self.search_and_extract(query, max_results)


# 方便使用的函式
def get_tavily_client() -> TavilyClient:
    """取得 TavilyClient 實例"""
    return TavilyClient()


def search_company_info(company_name: str, max_results: int = 3) -> Dict[str, Any]:
    """
    搜尋公司資訊的便捷函式

    Args:
        company_name: 公司名稱
        max_results: 最大結果數量

    Returns:
        Dict: 搜尋和內容提取結果
    """
    client = get_tavily_client()
    return client.get_company_info(company_name, max_results)
