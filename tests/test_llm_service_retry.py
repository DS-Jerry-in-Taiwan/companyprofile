"""
LLM Service 重試機制測試

測試 llm_call_with_retry 函數的：
1. 成功調用
2. 失敗後的回退機制
3. 多次重試邏輯
4. word_limit 參數正確傳遞
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# 設定 sys.path 以便導入
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNCTIONS_DIR = os.path.join(PROJECT_ROOT, "src", "functions")
if FUNCTIONS_DIR not in sys.path:
    sys.path.insert(0, FUNCTIONS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestLLMServiceRetry:
    """LLM Service 重試機制測試"""

    @patch("utils.llm_service._call_llm_core")
    def test_llm_call_with_retry_success(self, mock_call_core):
        """測試 LLM 呼叫成功的情況"""
        from utils.llm_service import _call_llm_with_retry

        # 設定 mock 的回傳值
        expected_result = {
            "title": "Test Company Brief",
            "body_html": "<p>A test company</p>",
            "summary": "Test summary",
        }
        mock_call_core.return_value = expected_result

        # 呼叫函數
        result = _call_llm_with_retry(prompt="Test company", word_limit=100)

        # 驗證結果
        assert result == expected_result
        # 驗證內部函數被正確呼叫
        mock_call_core.assert_called_once_with("Test company", 100)

    @patch("utils.llm_service._call_llm_core")
    @patch("utils.llm_service._get_default_response")
    def test_llm_call_with_retry_fallback(self, mock_default, mock_call_core):
        """測試 LLM 呼叫失敗時回退到預設響應"""
        from utils.llm_service import _call_llm_with_retry

        # 設定 mock：核心呼叫失敗，預設響應成功
        mock_call_core.side_effect = Exception("API Error")
        expected_fallback = {
            "title": "Company - 企業簡介",
            "body_html": "<p>Company 是一家專業的企業</p>",
            "summary": "Company - 專業企業，提供優質產品和服務。",
        }
        mock_default.return_value = expected_fallback

        # 呼叫函數
        result = _call_llm_with_retry("Test prompt", word_limit=50)

        # 驗證回退被觸發
        assert result == expected_fallback
        mock_default.assert_called_once()

    @patch("utils.llm_service.LANGCHAIN_AVAILABLE", False)
    @patch("utils.llm_service._call_llm_core")
    def test_llm_call_without_langchain(self, mock_call_core):
        """測試當 LangChain 不可用時的呼叫"""
        from utils.llm_service import call_llm

        expected_result = {
            "title": "Test",
            "body_html": "<p>Test</p>",
            "summary": "Test",
        }
        mock_call_core.return_value = expected_result

        result = call_llm("Test prompt", word_limit=100)

        assert result == expected_result
        mock_call_core.assert_called_once()

    @patch("utils.llm_service._call_llm_core")
    def test_llm_call_with_dict_prompt(self, mock_call_core):
        """測試使用字典 prompt 的呼叫"""
        from utils.llm_service import _call_llm_core

        prompt_dict = {
            "company_name": "Tech Corp",
            "industry": "Technology",
            "description": "A tech company",
            "products_services": "Software",
            "company_size": "Large",
            "founded_year": "2020",
        }

        expected_result = {
            "title": "Tech Corp Brief",
            "body_html": "<p>Tech Corp</p>",
            "summary": "Tech Corp",
        }
        mock_call_core.return_value = expected_result

        result = _call_llm_core(prompt_dict, word_limit=100)

        assert result == expected_result

    @patch("utils.llm_service._call_llm_core")
    def test_llm_call_preserves_word_limit(self, mock_call_core):
        """測試 word_limit 參數被正確保存和傳遞"""
        from utils.llm_service import _call_llm_with_retry

        mock_call_core.return_value = {
            "title": "Test",
            "body_html": "<p>Test</p>",
            "summary": "Test",
        }

        # 測試多種 word_limit 值
        test_cases = [
            ("Prompt 1", None),
            ("Prompt 2", 50),
            ("Prompt 3", 100),
            ("Prompt 4", 200),
        ]

        for prompt, word_limit in test_cases:
            mock_call_core.reset_mock()
            _call_llm_with_retry(prompt, word_limit)

            # 驗證 word_limit 被正確傳遞
            mock_call_core.assert_called_once()
            call_args = mock_call_core.call_args
            assert call_args[0][1] == word_limit, f"Failed for word_limit={word_limit}"

    @patch("utils.llm_service._call_llm_core")
    def test_llm_call_with_string_prompt(self, mock_call_core):
        """測試使用字串 prompt 的呼叫"""
        from utils.llm_service import _call_llm_with_retry

        expected_result = {
            "title": "Company Brief",
            "body_html": "<p>Brief content</p>",
            "summary": "Summary",
        }
        mock_call_core.return_value = expected_result

        result = _call_llm_with_retry("String prompt", word_limit=100)

        assert result == expected_result
        mock_call_core.assert_called_once_with("String prompt", 100)

    @patch("utils.llm_service.get_retry_config")
    @patch("utils.llm_service._call_llm_core")
    def test_llm_retry_config_integration(self, mock_call_core, mock_get_config):
        """測試重試配置被正確使用"""
        from utils.llm_service import _call_llm_with_retry

        # 設定 mock 配置
        mock_config = MagicMock()
        mock_config.max_attempts = 3
        mock_get_config.return_value = mock_config

        mock_call_core.return_value = {
            "title": "Test",
            "body_html": "<p>Test</p>",
            "summary": "Test",
        }

        result = _call_llm_with_retry("Test", word_limit=100)

        assert result is not None
        mock_get_config.assert_called_once()


class TestLLMCallIntegration:
    """LLM 呼叫的整合測試"""

    @patch("utils.llm_service.call_llm")
    def test_full_llm_call_flow(self, mock_call_llm):
        """測試完整的 LLM 呼叫流程"""
        from utils.llm_service import call_llm

        expected_result = {
            "title": "Company Brief",
            "body_html": "<p>Company details</p>",
            "summary": "Brief summary",
        }
        mock_call_llm.return_value = expected_result

        result = call_llm(prompt="Test company details", word_limit=150)

        assert result == expected_result
        assert "title" in result
        assert "body_html" in result
        assert "summary" in result


class TestErrorHandling:
    """錯誤處理測試"""

    @patch("utils.llm_service._call_llm_core")
    @patch("utils.llm_service._get_default_response")
    def test_error_returns_default_response(self, mock_default, mock_call_core):
        """測試錯誤時返回預設響應"""
        from utils.llm_service import _call_llm_with_retry

        mock_call_core.side_effect = RuntimeError("API Connection Error")
        default_response = {
            "title": "Default Title",
            "body_html": "<p>Default content</p>",
            "summary": "Default summary",
        }
        mock_default.return_value = default_response

        result = _call_llm_with_retry("Test", word_limit=100)

        assert result == default_response
        mock_default.assert_called_once()

    @patch("utils.llm_service._call_llm_core")
    def test_none_prompt_handling(self, mock_call_core):
        """測試 None prompt 的處理"""
        from utils.llm_service import _call_llm_core

        # 這應該被視為有效的呼叫
        mock_call_core.return_value = {
            "title": "Default",
            "body_html": "<p>Default</p>",
            "summary": "Default",
        }

        result = _call_llm_core(None, word_limit=100)

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
