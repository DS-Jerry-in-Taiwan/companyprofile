"""
Data Retrieval & Preprocessing Service
數據檢索與前處理服務的完整實作
"""

import logging
import time
import uuid
from typing import Optional, List
from datetime import datetime

import sys
import os

# 添加当前目录到路径，确保可以导入本地模块
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from .serper_search import SerperSearchProvider
from .web_scraper import WebScraper
from .text_cleaner import TextCleaner
from schemas.data_models import (
    CleanedData,
    SearchResult,
    ScrapedContent,
    PreprocessingRequest,
    PreprocessingResponse,
)
from pydantic import HttpUrl

logger = logging.getLogger(__name__)


class DataRetrievalService:
    """數據檢索與前處理服務"""

    def __init__(
        self,
        serper_api_key: Optional[str] = None,
        search_timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """
        初始化數據檢索服務

        Args:
            serper_api_key: Serper API 金鑰
            search_timeout: 搜尋超時時間
            verify_ssl: 是否驗證 SSL
        """
        self.search_provider = SerperSearchProvider(api_key=serper_api_key)
        self.scraper = WebScraper(timeout=search_timeout, verify_ssl=verify_ssl)
        self.cleaner = TextCleaner()

    def process_request(self, request: PreprocessingRequest) -> PreprocessingResponse:
        """
        處理前處理請求

        Args:
            request: 前處理請求

        Returns:
            PreprocessingResponse: 前處理回應
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # 執行搜尋
            search_results = self._perform_search(request)

            # 取得要爬取的 URL
            target_urls = self._get_target_urls(request, search_results)

            # 爬取並清洗內容
            cleaned_data_list = self._scrape_and_clean(target_urls, request)

            # 計算處理時間
            processing_time = (time.time() - start_time) * 1000

            return PreprocessingResponse(
                request_id=request_id,
                success=True,
                cleaned_data=cleaned_data_list,
                search_results=search_results,
                error_message=None,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            processing_time = (time.time() - start_time) * 1000

            return PreprocessingResponse(
                request_id=request_id,
                success=False,
                cleaned_data=None,
                search_results=None,
                error_message=str(e),
                processing_time_ms=processing_time,
            )

    def _perform_search(self, request: PreprocessingRequest) -> List[SearchResult]:
        """
        執行搜尋

        Args:
            request: 前處理請求

        Returns:
            List[SearchResult]: 搜尋結果列表
        """
        # 建立搜尋查詢
        query = request.search_query or f"{request.company_name} 公司介紹"

        if request.require_english:
            query += " company profile"

        try:
            # 執行搜尋並取得詳細結果
            detailed_results = self.search_provider.search_with_details(
                query=query, max_results=request.max_search_results
            )

            # 轉換為 SearchResult 模型
            search_results = []
            for result in detailed_results:
                search_results.append(
                    SearchResult(
                        url=result["url"],
                        title=result["title"],
                        snippet=result.get("snippet", ""),
                        position=result["position"],
                        search_query=query,
                        provider="serper",
                    )
                )

            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            # 如果搜尋失敗，使用備用 URL
            return []

    def _get_target_urls(
        self, request: PreprocessingRequest, search_results: List[SearchResult]
    ) -> List[str]:
        """
        取得要爬取的 URL 列表

        Args:
            request: 前處理請求
            search_results: 搜尋結果列表

        Returns:
            List[str]: URL 列表
        """
        urls = []

        # 優先使用參考 URL
        if request.reference_urls:
            urls.extend([str(url) for url in request.reference_urls])

        # 添加搜尋結果
        for result in search_results:
            if str(result.url) not in urls:
                urls.append(str(result.url))

        # 如果沒有 URL，使用公司網站
        if not urls and request.company_url:
            urls.append(str(request.company_url))

        return urls

    def _scrape_and_clean(
        self, urls: List[str], request: PreprocessingRequest
    ) -> List[CleanedData]:
        """
        爬取並清洗內容

        Args:
            urls: URL 列表
            request: 前處理請求

        Returns:
            List[CleanedData]: 清洗後的資料列表
        """
        cleaned_data_list = []

        for url in urls[:3]:  # 限制最多處理 3 個 URL
            try:
                # 爬取內容
                raw_content = self.scraper.extract(url)

                # 清洗文字
                cleaned_text = self.cleaner.clean_for_llm(raw_content, max_length=5000)

                # 如果內容太短，跳過
                if len(cleaned_text) < 50:
                    logger.warning(f"Content too short for {url}, skipping")
                    continue

                # 建立 CleanedData
                cleaned_data = CleanedData(
                    title=f"{request.company_name} - 資料來源",
                    source_url=HttpUrl(url),
                    content_text=cleaned_text,
                    token_count=None,
                    word_count=None,
                    char_count=None,
                    language=None,
                )

                # 計算統計資訊
                cleaned_data.calculate_counts()

                cleaned_data_list.append(cleaned_data)

            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue

        return cleaned_data_list

    def get_single_page_content(self, url: str) -> Optional[CleanedData]:
        """
        取得單一頁面的內容

        Args:
            url: 目標 URL

        Returns:
            Optional[CleanedData]: 清洗後的資料
        """
        try:
            # 爬取內容
            raw_content = self.scraper.extract(url)

            # 清洗文字
            cleaned_text = self.cleaner.clean_for_llm(raw_content, max_length=5000)

            # 建立 CleanedData
            cleaned_data = CleanedData(
                title="單頁面內容",
                source_url=HttpUrl(url),
                content_text=cleaned_text,
                token_count=None,
                word_count=None,
                char_count=None,
                language=None,
            )

            # 計算統計資訊
            cleaned_data.calculate_counts()

            return cleaned_data

        except Exception as e:
            logger.error(f"Error getting content from {url}: {e}")
            return None


# 便利函數
def create_data_retrieval_service(
    serper_api_key: Optional[str] = None,
) -> DataRetrievalService:
    """
    建立數據檢索服務實例

    Args:
        serper_api_key: Serper API 金鑰

    Returns:
        DataRetrievalService: 數據檢索服務實例
    """
    return DataRetrievalService(serper_api_key=serper_api_key)


def process_company_data_retrieval(
    company_name: str,
    company_url: Optional[str] = None,
    search_query: Optional[str] = None,
    serper_api_key: Optional[str] = None,
) -> PreprocessingResponse:
    """
    處理公司資料檢索的便利函數

    Args:
        company_name: 公司名稱
        company_url: 公司網站 URL
        search_query: 自定義搜尋查詢
        serper_api_key: Serper API 金鑰

    Returns:
        PreprocessingResponse: 前處理回應
    """
    service = create_data_retrieval_service(serper_api_key)

    request = PreprocessingRequest(
        company_name=company_name,
        company_url=company_url,
        search_query=search_query,
        reference_urls=None,
    )

    return service.process_request(request)
