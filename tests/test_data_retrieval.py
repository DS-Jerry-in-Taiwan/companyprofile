"""
Unit Tests for Data Retrieval & Preprocessing Module
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from schemas.data_models import (
    CleanedData,
    SearchResult,
    ScrapedContent,
    PreprocessingRequest,
    PreprocessingResponse,
)
from services.text_cleaner import TextCleaner, TextSplitter


class TestCleanedData:
    """CleanedData 模型測試"""

    def test_create_cleaned_data(self):
        """測試建立 CleanedData"""
        data = CleanedData(
            title="測試標題",
            source_url="https://example.com",
            content_text="這是測試內容",
        )

        assert data.title == "測試標題"
        # HttpUrl 會自動添加尾部斜線
        assert str(data.source_url) == "https://example.com/"
        assert data.content_text == "這是測試內容"

    def test_calculate_counts(self):
        """測試計算統計資訊"""
        data = CleanedData(
            title="測試",
            source_url="https://example.com",
            content_text="這是測試內容，包含中文和English words",
        )

        data.calculate_counts()

        assert data.char_count > 0
        assert data.word_count > 0
        assert data.token_count > 0

    def test_validate_empty_title(self):
        """測試空標題驗證"""
        with pytest.raises(ValueError):
            CleanedData(
                title="", source_url="https://example.com", content_text="測試內容"
            )

    def test_validate_empty_content(self):
        """測試空內容驗證"""
        with pytest.raises(ValueError):
            CleanedData(title="標題", source_url="https://example.com", content_text="")


class TestSearchResult:
    """SearchResult 模型測試"""

    def test_create_search_result(self):
        """測試建立 SearchResult"""
        result = SearchResult(
            url="https://example.com",
            title="測試標題",
            snippet="測試摘要",
            position=1,
            search_query="測試查詢",
            provider="serper",
        )

        assert result.position == 1
        assert result.provider == "serper"

    def test_clean_snippet(self):
        """測試摘要清洗"""
        result = SearchResult(
            url="https://example.com",
            title="標題",
            snippet="  這是  多餘空白  的測試  ",
            position=1,
            search_query="查詢",
            provider="test",
        )

        assert "  " not in result.snippet


class TestPreprocessingRequest:
    """PreprocessingRequest 模型測試"""

    def test_create_request(self):
        """測試建立請求"""
        request = PreprocessingRequest(
            company_name="測試公司", company_url="https://test.com"
        )

        assert request.company_name == "測試公司"
        assert request.max_search_results == 5  # 預設值

    def test_max_results_limit(self):
        """測試最大結果數限制"""
        import pytest

        # 超過上限的值應該拋出 ValidationError
        with pytest.raises(Exception):  # PydanticValidationError
            PreprocessingRequest(
                company_name="測試",
                max_search_results=100,  # 上限是 20
            )


class TestTextCleaner:
    """TextCleaner 服務測試"""

    def test_basic_clean(self):
        """測試基本清洗"""
        cleaner = TextCleaner()
        text = "  這是  測試  文字  "

        result = cleaner.clean(text)

        assert "  " not in result
        assert result == "這是 測試 文字"

    def test_remove_html_entities(self):
        """測試移除 HTML 實體"""
        cleaner = TextCleaner()
        text = "測試&nbsp;內容&amp;符號"

        result = cleaner.clean(text)

        assert "&nbsp;" not in result
        assert "&amp;" not in result

    def test_remove_urls(self):
        """測試移除 URL"""
        cleaner = TextCleaner()
        text = "測試 https://example.com 內容"

        result = cleaner.clean(text)

        assert "https://" not in result

    def test_count_tokens_estimate(self):
        """測試 token 數量估算"""
        cleaner = TextCleaner()
        text = "這是一段中文測試文字和 English text mixed together"

        tokens = cleaner.count_tokens_estimate(text)

        assert tokens > 0


class TestTextSplitter:
    """TextSplitter 服務測試"""

    def test_split_short_text(self):
        """測試分割短文字"""
        splitter = TextSplitter(chunk_size=100)
        text = "這是一段短文字"

        result = splitter.split(text)

        assert len(result) == 1
        assert result[0] == text

    def test_split_long_text(self):
        """測試分割長文字"""
        splitter = TextSplitter(chunk_size=50, overlap=10)
        text = "這是一段很長的文字。" * 10

        result = splitter.split(text)

        assert len(result) > 1


class TestPreprocessingResponse:
    """PreprocessingResponse 模型測試"""

    def test_success_response(self):
        """測試成功回應"""
        response = PreprocessingResponse(
            request_id="test-123",
            success=True,
            cleaned_data=[],
            processing_time_ms=100.0,
        )

        assert response.success is True
        assert response.error_message is None

    def test_error_response(self):
        """測試錯誤回應"""
        response = PreprocessingResponse(
            request_id="test-456", success=False, error_message="發生錯誤"
        )

        assert response.success is False
        assert response.error_message == "發生錯誤"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
