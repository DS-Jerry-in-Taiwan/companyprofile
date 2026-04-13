"""
Phase 14 Stage 3: 字數檢核模組測試

測試目標：
1. 驗證 WordCountValidator 的基本功能
2. 驗證字數範圍檢核
3. 驗證重寫提示生成
4. 驗證便捷函數
5. 驗證邊界情況
"""

import pytest
import sys
import os
import re

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.functions.utils.word_count_validator import (
    WordCountValidator,
    ValidationResult,
    WORD_COUNT_RANGES,
    REWRITE_THRESHOLD,
    MAX_REWRITE_ATTEMPTS,
    count_words_in_html,
    validate_word_count,
    needs_rewrite,
)


# ===== 測試資料 =====

CONCISE_RANGE = WORD_COUNT_RANGES["concise"]
STANDARD_RANGE = WORD_COUNT_RANGES["standard"]
DETAILED_RANGE = WORD_COUNT_RANGES["detailed"]


# ===== 1. 基本功能測試 =====


class TestWordCountValidatorBasic:
    """WordCountValidator 基本功能測試"""

    def test_validator_initialization(self):
        """測試驗證器初始化"""
        validator = WordCountValidator()
        assert validator is not None
        assert validator.ranges == WORD_COUNT_RANGES
        assert validator.rewrite_threshold == REWRITE_THRESHOLD
        assert validator.max_rewrite_attempts == MAX_REWRITE_ATTEMPTS

    def test_validator_custom_ranges(self):
        """測試自定義字數範圍"""
        custom_ranges = {
            "concise": {"min": 50, "max": 100},
            "standard": {"min": 150, "max": 200},
        }
        validator = WordCountValidator(ranges=custom_ranges)
        assert validator.ranges == custom_ranges

    def test_validator_custom_threshold(self):
        """測試自定義重寫閾值"""
        validator = WordCountValidator(rewrite_threshold=0.15)
        assert validator.rewrite_threshold == 0.15

    def test_validator_custom_max_attempts(self):
        """測試自定義最大重寫次數"""
        validator = WordCountValidator(max_rewrite_attempts=3)
        assert validator.max_rewrite_attempts == 3


# ===== 2. 字數計算測試 =====


class TestWordCountCalculation:
    """字數計算測試"""

    def test_count_words_plain_text(self):
        """測試純文字字數計算"""
        validator = WordCountValidator()
        text = "這是一段測試文字"
        # 這是一段測試文字 = 8 個字
        assert validator.count_words(text) == 8

    def test_count_words_with_html(self):
        """測試含 HTML 標籤的字數計算"""
        validator = WordCountValidator()
        html = "<p>這是一段測試文字</p>"
        # 應移除 HTML 標籤，只計算純文字 = 8 個字
        assert validator.count_words(html) == 8

    def test_count_words_empty_string(self):
        """測試空字串"""
        validator = WordCountValidator()
        assert validator.count_words("") == 0

    def test_count_words_none(self):
        """測試 None 值"""
        validator = WordCountValidator()
        assert validator.count_words(None) == 0

    def test_count_words_with_extra_whitespace(self):
        """測試含多餘空白"""
        validator = WordCountValidator()
        text = "這 是 一 段 測 試 文 字"
        # 移除空白後 = 8 個字
        assert validator.count_words(text) == 8

    def test_count_words_complex_html(self):
        """測試複雜 HTML 結構"""
        validator = WordCountValidator()
        html = """
        <div>
            <p>第一段文字</p>
            <p>第二段文字</p>
            <ul>
                <li>列表項目一</li>
                <li>列表項目二</li>
            </ul>
        </div>
        """
        # 應正確計算所有文字
        # 第一段文字(5) + 第二段文字(5) + 列表項目一(5) + 列表項目二(5) = 20
        result = validator.count_words(html)
        assert result == 20

    def test_count_words_nested_html(self):
        """測試巢狀 HTML"""
        validator = WordCountValidator()
        html = "<div><p><span>巢狀標籤內的文字</span></p></div>"
        # 巢狀標籤內的文字 = 8 個字
        assert validator.count_words(html) == 8


# ===== 3. 字數範圍檢核測試 =====


class TestWordCountValidation:
    """字數範圍檢核測試"""

    def test_validate_concise_in_range(self):
        """測試精簡模板在範圍內"""
        validator = WordCountValidator()
        # 這是測試文字 = 8 字，8 * 8 = 64 字，在 40-120 範圍內
        html = "<p>" + "這是測試文字。" * 8 + "</p>"
        result = validator.validate(html, "concise")
        assert result.is_valid is True
        assert result.min_range == CONCISE_RANGE["min"]
        assert result.max_range == CONCISE_RANGE["max"]

    def test_validate_standard_in_range(self):
        """測試標準模板在範圍內"""
        validator = WordCountValidator()
        # 這是測試文字 = 7 字，7 * 20 = 140 字，在 130-230 範圍內
        html = "<p>" + "這是測試文字。" * 20 + "</p>"
        result = validator.validate(html, "standard")
        assert result.is_valid is True

    def test_validate_detailed_in_range(self):
        """測試詳細模板在範圍內"""
        validator = WordCountValidator()
        # 這是測試文字 = 7 字，7 * 50 = 350 字，在 280-550 範圍內
        html = "<p>" + "這是測試文字。" * 50 + "</p>"
        result = validator.validate(html, "detailed")
        assert result.is_valid is True

    def test_validate_concise_below_min(self):
        """測試精簡模板低於下限"""
        validator = WordCountValidator()
        html = "<p>短內容</p>"  # 4 字，低於 40 字下限
        result = validator.validate(html, "concise")
        assert result.is_valid is False
        assert result.word_count < result.min_range

    def test_validate_concise_above_max(self):
        """測試精簡模板高於上限"""
        validator = WordCountValidator()
        # 這是測試文字 = 7 字，7 * 17 + 5 = 124，需要再多一點才能高於 120
        html = "<p>" + "這是測試文字。" * 17 + "ABCDE" + "</p>"  # 124
        result = validator.validate(html, "concise")
        assert result.is_valid is False
        assert result.word_count > result.max_range

    def test_validate_empty_content(self):
        """測試空內容"""
        validator = WordCountValidator()
        result = validator.validate("", "concise")
        assert result.is_valid is False
        assert result.word_count == 0

    def test_validate_none_content(self):
        """測試 None 內容"""
        validator = WordCountValidator()
        result = validator.validate(None, "standard")
        assert result.is_valid is False

    def test_validate_case_insensitive_template_type(self):
        """測試模板類型大小寫不敏感"""
        validator = WordCountValidator()
        html = "<p>" + "這是測試文字。" * 8 + "</p>"  # 64 字，在 40-120 範圍內
        result_lower = validator.validate(html, "concise")
        result_upper = validator.validate(html, "CONCISE")
        result_mixed = validator.validate(html, "Concise")
        assert result_lower.is_valid == result_upper.is_valid == result_mixed.is_valid


# ===== 4. 重寫判斷測試 =====


class TestRewriteDecision:
    """重寫判斷測試"""

    def test_needs_rewrite_above_threshold(self):
        """測試超出閾值需要重寫"""
        validator = WordCountValidator()
        # 精簡模板 146 字，超出 120 上限 (偏離 21.7% > 20%)
        # "這是測試文字。" = 7 字，7 * 20 + 6 = 146 字
        html = "<p>" + "這是測試文字。" * 20 + "ABCDEF" + "</p>"  # 146 字
        result = validator.validate(html, "concise")
        # 偏離 (146-120)/120 = 21.7% > 20% 閾值
        assert validator.needs_rewrite(result) is True

    def test_needs_rewrite_below_threshold(self):
        """測試低於閾值不需要重寫"""
        validator = WordCountValidator()
        # 精簡模板 125 字，超出 120 上限 (偏離 4.17%)
        # 7 * 17 + 5 = 124 字
        html = "<p>" + "這是測試文字。" * 17 + "ABCDE" + "</p>"  # 124 字
        result = validator.validate(html, "concise")
        # 偏離 (124-120)/120 = 3.3% < 20% 閾值
        assert validator.needs_rewrite(result) is False

    def test_needs_rewrite_in_range(self):
        """測試在範圍內不需要重寫"""
        validator = WordCountValidator()
        html = "<p>" + "這是測試文字。" * 8 + "</p>"  # 56 字
        result = validator.validate(html, "concise")
        assert validator.needs_rewrite(result) is False

    def test_needs_rewrite_below_min_threshold(self):
        """測試低於下限但在閾值內不需要重寫"""
        validator = WordCountValidator()
        # 精簡模板 36 字，低於 40 下限 (偏離 10% < 20%)
        html = "<p>" + "這是測試文字。" * 5 + "C" + "</p>"  # 36 字
        result = validator.validate(html, "concise")
        # 偏離 (40-36)/40 = 10% < 20% 閾值
        assert validator.needs_rewrite(result) is False

    def test_needs_rewrite_in_range(self):
        """測試在範圍內不需要重寫"""
        validator = WordCountValidator()
        html = "<p>" + "這是測試文字。" * 8 + "</p>"  # 64 字
        result = validator.validate(html, "concise")
        assert validator.needs_rewrite(result) is False

    def test_needs_rewrite_below_min_threshold(self):
        """測試低於下限但在閾值內不需要重寫"""
        validator = WordCountValidator()
        # 精簡模板 36 字，低於 40 下限 (偏離 10% < 20%)
        html = "<p>" + "這是測試文字。" * 5 + "C" + "</p>"  # 36 字
        result = validator.validate(html, "concise")
        # 偏離 (40-36)/40 = 10% < 20% 閾值
        assert validator.needs_rewrite(result) is False


# ===== 5. 重寫 Prompt 生成測試 =====


class TestRewritePromptGeneration:
    """重寫 Prompt 生成測試"""

    def test_build_rewrite_prompt_shorten(self):
        """測試需要縮短的重寫 Prompt"""
        validator = WordCountValidator()
        html = "<p>" + "這是測試文字。" * 15 + "</p>"  # 約 150 字
        prompt = validator.build_rewrite_prompt(html, "concise", 150, (40, 120), 0)
        # 應包含目標範圍
        assert "40-120" in prompt
        assert "150" in prompt
        assert "縮短" in prompt
        # 應包含保留要求
        assert "保留" in prompt
        assert "核心資訊" in prompt

    def test_build_rewrite_prompt_expand(self):
        """測試需要擴展的重寫 Prompt"""
        validator = WordCountValidator()
        html = "<p>短內容</p>"  # 4 字
        prompt = validator.build_rewrite_prompt(html, "standard", 4, (130, 230), 0)
        # 應包含目標範圍
        assert "130-230" in prompt
        assert "4" in prompt
        assert "擴展" in prompt

    def test_build_rewrite_prompt_rewrite_count(self):
        """測試重寫次數"""
        validator = WordCountValidator()
        html = "<p>" + "這是測試文字。" * 15 + "</p>"  # 約 150 字
        prompt1 = validator.build_rewrite_prompt(html, "concise", 150, (40, 120), 0)
        prompt2 = validator.build_rewrite_prompt(html, "concise", 150, (40, 120), 1)
        # 應該包含不同的重寫次數標記
        assert "第 1 次" in prompt1
        assert "第 2 次" in prompt2

    def test_build_rewrite_prompt_contains_requirements(self):
        """測試重寫 Prompt 包含所有要求"""
        validator = WordCountValidator()
        html = "<p>測試內容</p>"
        prompt = validator.build_rewrite_prompt(html, "standard", 5, (130, 230), 0)
        # 應包含禁止事項
        assert "禁止" in prompt
        # 應包含台灣用語要求
        assert "台灣" in prompt
        # 應包含保留核心資訊要求
        assert "核心資訊" in prompt


# ===== 6. 便捷函數測試 =====


class TestConvenienceFunctions:
    """便捷函數測試"""

    def test_count_words_in_html_function(self):
        """測試 count_words_in_html 便捷函數"""
        html = "<p>測試內容</p>"
        result = count_words_in_html(html)
        # "測試內容" = 4 個字
        assert result == 4

    def test_validate_word_count_function(self):
        """測試 validate_word_count 便捷函數"""
        html = "<p>" + "這是測試文字。" * 10 + "</p>"  # 70 字，在 40-120 範圍內
        result = validate_word_count(html, "concise")
        assert result.is_valid is True
        assert result.word_count >= CONCISE_RANGE["min"]
        assert result.word_count <= CONCISE_RANGE["max"]

    def test_validate_word_count_with_custom_ranges(self):
        """測試 validate_word_count 自定義範圍"""
        html = "<p>" + "這是測試文字。" * 8 + "</p>"  # 56 字
        custom_ranges = {"concise": {"min": 50, "max": 100}}
        result = validate_word_count(html, "concise", ranges=custom_ranges)
        assert result.is_valid is True
        assert result.min_range == 50
        assert result.max_range == 100

    def test_needs_rewrite_function(self):
        """測試 needs_rewrite 便捷函數"""
        # "這是測試文字。" = 7 字，7 * 20 + 6 = 146 字，超出 120 上限
        html = "<p>" + "這是測試文字。" * 20 + "ABCDEF" + "</p>"  # 146 字
        result = validate_word_count(html, "concise")
        # 偏離 (146-120)/120 = 21.7% > 20% 閾值
        assert needs_rewrite(result) is True


# ===== 7. 模板範圍測試 =====


class TestTemplateRanges:
    """模板範圍測試"""

    def test_get_template_range_concise(self):
        """測試取得精簡模板範圍"""
        validator = WordCountValidator()
        min_range, max_range = validator.get_template_range("concise")
        assert min_range == 40
        assert max_range == 120

    def test_get_template_range_standard(self):
        """測試取得標準模板範圍"""
        validator = WordCountValidator()
        min_range, max_range = validator.get_template_range("standard")
        assert min_range == 130
        assert max_range == 230

    def test_get_template_range_detailed(self):
        """測試取得詳細模板範圍"""
        validator = WordCountValidator()
        min_range, max_range = validator.get_template_range("detailed")
        assert min_range == 280
        assert max_range == 550

    def test_get_template_range_unknown_fallback(self):
        """測試未知模板回退到標準"""
        validator = WordCountValidator()
        min_range, max_range = validator.get_template_range("unknown")
        assert min_range == STANDARD_RANGE["min"]
        assert max_range == STANDARD_RANGE["max"]


# ===== 8. 驗證並建議測試 =====


class TestValidateAndSuggest:
    """驗證並提供建議測試"""

    def test_validate_and_suggest_in_range(self):
        """測試在範圍內的建議"""
        validator = WordCountValidator()
        html = "<p>" + "這是測試文字。" * 8 + "</p>"  # 約 80 字
        result = validator.validate_and_suggest(html, "concise")
        assert result["is_valid"] is True
        assert len(result["suggestions"]) > 0
        assert "符合要求" in result["suggestions"][0]

    def test_validate_and_suggest_below_min(self):
        """測試低於下限的建議"""
        validator = WordCountValidator()
        html = "<p>短內容</p>"  # 4 字
        result = validator.validate_and_suggest(html, "concise")
        assert result["is_valid"] is False
        assert "過短" in result["suggestions"][0]
        assert result["needs_rewrite"] is True

    def test_validate_and_suggest_above_max(self):
        """測試高於上限的建議"""
        validator = WordCountValidator()
        # "這是測試文字。" = 7 字，7 * 20 + 6 = 146 字
        html = "<p>" + "這是測試文字。" * 20 + "ABCDEF" + "</p>"  # 146 字
        result = validator.validate_and_suggest(html, "concise")
        assert result["is_valid"] is False
        assert "過長" in result["suggestions"][0]
        assert result["needs_rewrite"] is True


# ===== 9. 邊界情況測試 =====


class TestBoundaryCases:
    """邊界情況測試"""

    def test_at_exact_min_boundary(self):
        """測試精確達到下限"""
        validator = WordCountValidator()
        # 精簡模板下限是 40
        text = "測" * 40
        html = f"<p>{text}</p>"
        result = validator.validate(html, "concise")
        assert result.is_valid is True

    def test_at_exact_max_boundary(self):
        """測試精確達到上限"""
        validator = WordCountValidator()
        # 精簡模板上限是 120
        text = "測" * 120
        html = f"<p>{text}</p>"
        result = validator.validate(html, "concise")
        assert result.is_valid is True

    def test_one_char_beyond_max(self):
        """測試超出上限一個字"""
        validator = WordCountValidator()
        text = "測" * 121
        html = f"<p>{text}</p>"
        result = validator.validate(html, "concise")
        assert result.is_valid is False
        # 偏離 1/120 = 0.83% < 20%，不需要重寫
        assert validator.needs_rewrite(result) is False

    def test_mixed_chinese_english(self):
        """測試中英文混合"""
        validator = WordCountValidator()
        html = "<p>這是Test內容123</p>"
        result = validator.validate(html, "concise")
        # 應正確計算（中文、英文、數字都算字）
        # 這(1)是(2)T(3)e(4)s(5)t(6)內(7)容(8)1(9)2(10)3(11) = 11 個字
        assert result.word_count == 11

    def test_all_whitespace(self):
        """測試全空白內容"""
        validator = WordCountValidator()
        result = validator.validate("   ", "concise")
        assert result.word_count == 0
        assert result.is_valid is False


# ===== 10. ValidationResult 資料類別測試 =====


class TestValidationResultDataclass:
    """ValidationResult 資料類別測試"""

    def test_validation_result_creation(self):
        """測試 ValidationResult 創建"""
        result = ValidationResult(
            is_valid=True,
            word_count=80,
            min_range=40,
            max_range=120,
            needs_rewrite=False,
        )
        assert result.is_valid is True
        assert result.word_count == 80
        assert result.needs_rewrite is False

    def test_validation_result_with_rewrite_info(self):
        """測試帶重寫資訊的 ValidationResult"""
        result = ValidationResult(
            is_valid=False,
            word_count=150,
            min_range=40,
            max_range=120,
            needs_rewrite=True,
            rewrite_reason="超出上限 25%",
            deviation=0.25,
        )
        assert result.needs_rewrite is True
        assert result.rewrite_reason == "超出上限 25%"
        assert result.deviation == 0.25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
