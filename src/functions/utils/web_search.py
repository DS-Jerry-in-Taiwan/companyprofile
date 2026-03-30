"""
Web Search Service
使用 Serper.dev API 的搜尋服務
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_search_provider():
    """取得搜尋服務實例"""
    from src.services.serper_search import SerperSearchProvider

    api_key = os.getenv("SERPER_API_KEY")
    return SerperSearchProvider(api_key=api_key)


def web_search(company_name, company_url=None, max_results=5):
    """
    執行網路搜尋，回傳公司相關 URL 列表

    Args:
        company_name: 公司名稱
        company_url: 公司網站 URL (可選)
        max_results: 最大回傳結果數量

    Returns:
        list: URL 列表
    """
    if company_url:
        return [company_url]

    try:
        provider = get_search_provider()
        query = f"{company_name} 官網"
        results = provider.search(query, max_results=max_results)
        return [result.url for result in results]

    except Exception as e:
        raise RuntimeError(f"Web search failed: {str(e)}")
