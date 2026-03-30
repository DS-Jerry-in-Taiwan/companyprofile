"""
Unit Tests for Data Retrieval Service
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.data_retrieval_service import (
    DataRetrievalService,
    create_data_retrieval_service,
    process_company_data_retrieval,
)
from schemas.data_models import PreprocessingRequest, PreprocessingResponse


class TestDataRetrievalService:
    """DataRetrievalService 測試"""

    def test_init(self):
        """測試初始化"""
        service = DataRetrievalService(serper_api_key="test_key")
        assert service.search_provider is not None
        assert service.scraper is not None
        assert service.cleaner is not None

    @patch("services.data_retrieval_service.SerperSearchProvider")
    @patch("services.data_retrieval_service.WebScraper")
    def test_process_request_success(self, mock_scraper_cls, mock_search_cls):
        """測試成功處理請求"""
        # Setup mocks
        mock_search = Mock()
        mock_search.search_with_details.return_value = [
            {
                "position": 1,
                "title": "Test Article",
                "url": "https://example.com",
                "snippet": "Test snippet",
                "displayed_url": "example.com",
            }
        ]
        mock_search_cls.return_value = mock_search

        mock_scraper = Mock()
        mock_scraper.extract.return_value = (
            "這是一段測試內容，用於測試數據檢索服務的功能是否正常運作。"
        )
        mock_scraper_cls.return_value = mock_scraper

        service = DataRetrievalService(serper_api_key="test_key")

        request = PreprocessingRequest(
            company_name="測試公司",
            company_url="https://test.com",
            max_search_results=5,
        )

        response = service.process_request(request)

        assert response.success is True
        assert response.request_id is not None
        assert response.processing_time_ms is not None

    @patch("services.data_retrieval_service.SerperSearchProvider")
    @patch("services.data_retrieval_service.WebScraper")
    def test_process_request_with_reference_urls(
        self, mock_scraper_cls, mock_search_cls
    ):
        """測試使用參考 URL"""
        mock_search = Mock()
        mock_search_cls.return_value = mock_search

        mock_scraper = Mock()
        mock_scraper.extract.return_value = (
            "這是一段測試內容，用於測試數據檢索服務的功能是否正常運作。"
        )
        mock_scraper_cls.return_value = mock_scraper

        service = DataRetrievalService(serper_api_key="test_key")

        request = PreprocessingRequest(
            company_name="測試公司", reference_urls=["https://reference.com"]
        )

        response = service.process_request(request)

        assert response.success is True
        # 應該優先使用參考 URL
        mock_scraper.extract.assert_called()

    @patch("services.data_retrieval_service.SerperSearchProvider")
    @patch("services.data_retrieval_service.WebScraper")
    def test_get_single_page_content(self, mock_scraper_cls, mock_search_cls):
        """測試取得單一頁面內容"""
        mock_scraper = Mock()
        mock_scraper.extract.return_value = (
            "這是一段測試內容，用於測試數據檢索服務的功能是否正常運作。"
        )
        mock_scraper_cls.return_value = mock_scraper

        service = DataRetrievalService(serper_api_key="test_key")

        result = service.get_single_page_content("https://example.com")

        assert result is not None
        assert result.source_url is not None
        assert len(result.content_text) > 0


class TestConvenienceFunctions:
    """便利函數測試"""

    def test_create_data_retrieval_service(self):
        """測試建立服務實例"""
        service = create_data_retrieval_service(serper_api_key="test_key")
        assert service is not None
        assert isinstance(service, DataRetrievalService)

    @patch("services.data_retrieval_service.SerperSearchProvider")
    @patch("services.data_retrieval_service.DataRetrievalService.process_request")
    def test_process_company_data_retrieval(self, mock_process, mock_search_cls):
        """測試便利函數"""
        mock_process.return_value = PreprocessingResponse(
            request_id="test", success=True, cleaned_data=[], processing_time_ms=100.0
        )

        response = process_company_data_retrieval(
            company_name="測試公司", company_url="https://test.com"
        )

        assert response.success is True
        mock_process.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
