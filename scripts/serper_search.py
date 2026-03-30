import requests
import os
import logging

logger = logging.getLogger(__name__)


def search_serper(query, max_results=5):
    """
    執行搜尋並回傳 URL 列表

    Args:
        query: 搜尋查詢字串
        max_results: 最大回傳結果數量

    Returns:
        List[str]: URL 列表
    """
    api_key = os.getenv("SERPER_API_KEY", "")

    # 如果沒有 API 金鑰或是 dummy_value，使用 mock 搜尋
    if not api_key or api_key == "dummy_value":
        return _mock_search(query, max_results)

    api_url = "https://google.serper.dev/search"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
    }
    data = {
        "q": query,
        "gl": "tw",
        "hl": "zh",
        "num": max_results,
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=10)
        response.raise_for_status()

        data = response.json()
        urls = []

        for result in data.get("organic", [])[:max_results]:
            if "link" in result:
                urls.append(result["link"])

        return urls

    except requests.exceptions.RequestException as e:
        logger.error(f"Search API error: {e}")
        # API 請求失敗時，使用 mock 搜尋
        return _mock_search(query, max_results)


def _mock_search(query, max_results=5):
    """
    提供 mock 搜尋結果，用於測試或 API 失敗時

    Args:
        query: 搜尋查詢字串
        max_results: 最大回傳結果數量

    Returns:
        List[str]: 模擬的 URL 列表
    """
    logger.info(f"Using mock search for query: {query}")

    # 根據查詢返回一些模擬結果
    mock_results = [
        f"https://example.com/article/1?q={query}",
        f"https://example.com/article/2?q={query}",
        f"https://example.com/article/3?q={query}",
        f"https://example.com/news?q={query}",
        f"https://example.com/blog?q={query}",
    ]

    return mock_results[:max_results]
