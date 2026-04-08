"""
測試字數截斷功能
"""

import pytest
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.functions.utils.text_truncate import (
    count_chinese_characters,
    truncate_text,
    truncate_llm_output,
)


class TestCountChineseCharacters:
    """測試中文字數計算"""

    def test_pure_chinese(self):
        """測試純中文字符計算"""
        text = "這是一段測試文字"
        assert count_chinese_characters(text) == 8

    def test_mixed_content(self):
        """測試混合內容（中英文、數字、標點）"""
        text = "公司成立於2020年，專注AI技術！"
        assert count_chinese_characters(text) > 0

    def test_with_html(self):
        """測試包含 HTML 標籤的文本"""
        text = "<p>這是一段測試文字</p>"
        # HTML 標籤會被移除
        assert count_chinese_characters(text) == 8

    def test_empty_string(self):
        """測試空字符串"""
        assert count_chinese_characters("") == 0


class TestTruncateText:
    """測試文本截斷"""

    def test_no_truncation_needed(self):
        """測試無需截斷的情況"""
        text = "短文本"
        result = truncate_text(text, 10)
        assert result == text

    def test_simple_truncation(self):
        """測試簡單截斷"""
        text = "這是一段很長的測試文字需要被截斷"
        result = truncate_text(text, 10, preserve_html=False)
        assert len(result) == 10

    def test_html_truncation(self):
        """測試 HTML 文本截斷"""
        text = "<p>這是一段很長的測試文字需要被截斷</p>"
        result = truncate_text(text, 10, preserve_html=True)
        # 截斷後應該仍然是有效的 HTML
        assert "<p>" in result or "<" in result

    def test_none_word_limit(self):
        """測試 word_limit 為 None"""
        text = "測試文本"
        result = truncate_text(text, None)
        assert result == text


class TestTruncateLLMOutput:
    """測試 LLM 輸出截斷"""

    def test_truncate_body_html(self):
        """測試 body_html 截斷"""
        output = {
            "title": "公司標題",
            "body_html": "<p>" + "這是一段很長的內容" * 20 + "</p>",
            "summary": "簡短摘要",
        }
        result = truncate_llm_output(output, 50)
        assert count_chinese_characters(result["body_html"]) <= 50

    def test_truncate_summary(self):
        """測試 summary 截斷"""
        output = {
            "title": "公司標題",
            "body_html": "<p>內容</p>",
            "summary": "這是一段很長的摘要內容" * 10,
        }
        result = truncate_llm_output(output, 100)
        # summary 應該被截斷到較小的限制
        assert count_chinese_characters(result["summary"]) <= 50

    def test_truncate_title(self):
        """測試 title 截斷"""
        output = {
            "title": "這是一個非常長的公司標題需要被截斷" * 3,
            "body_html": "<p>內容</p>",
            "summary": "摘要",
        }
        result = truncate_llm_output(output, 100)
        # title 應該不超過 50 字
        assert count_chinese_characters(result["title"]) <= 50

    def test_no_word_limit(self):
        """測試沒有 word_limit 的情況"""
        output = {
            "title": "標題",
            "body_html": "<p>內容</p>",
            "summary": "摘要",
        }
        result = truncate_llm_output(output, None)
        assert result == output

    def test_all_fields_within_limit(self):
        """測試所有欄位都在限制內"""
        output = {
            "title": "短標題",
            "body_html": "<p>短內容</p>",
            "summary": "短摘要",
        }
        result = truncate_llm_output(output, 100)
        # 不需要截斷
        assert result["title"] == output["title"]
        assert result["summary"] == output["summary"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
