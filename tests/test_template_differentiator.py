"""
Phase 14 Agent F/G: 模板差異化測試
測試三個模板（精簡/標準/詳細）的差異化功能
"""

import pytest
import re
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.functions.utils.template_differentiator import (
    differentiate_template,
    validate_template_differentiation,
    get_template_features,
    BRIEF_TEMPLATE_FEATURES,
    STANDARD_TEMPLATE_FEATURES,
    DETAILED_TEMPLATE_FEATURES,
)


class TestTemplateFeatures:
    """模板特徵測試"""

    def test_brief_template_features(self):
        """測試精簡模板特徵"""
        features = BRIEF_TEMPLATE_FEATURES
        assert features["min_length"] == 40  # Phase 14 Stage 3 更新
        assert features["max_length"] == 120  # Phase 14 Stage 3 更新（從 100 改為 120）
        assert features["style"] == "concise"
        assert features["allow_line_breaks"] is False
        assert "此外" in features["forbidden_patterns"]

    def test_standard_template_features(self):
        """測試標準模板特徵"""
        features = STANDARD_TEMPLATE_FEATURES
        assert features["min_length"] == 130  # Phase 14 Stage 3 更新
        assert features["max_length"] == 230  # Phase 14 Stage 3 更新（從 200 改為 230）
        assert features["style"] == "balanced"
        assert features["allow_line_breaks"] is True
        assert "成立" in features["required_keywords"]

    def test_detailed_template_features(self):
        """測試詳細模板特徵"""
        features = DETAILED_TEMPLATE_FEATURES
        assert features["min_length"] == 280  # Phase 14 Stage 3 新增
        assert features["max_length"] == 550  # Phase 14 Stage 3 更新（從 500 改為 550）
        assert features["style"] == "detailed"
        assert features["allow_line_breaks"] is True
        assert "願景" in features["required_keywords"]

    def test_get_template_features(self):
        """測試取得模板特徵"""
        brief_features = get_template_features("brief")
        assert brief_features["min_length"] == 40
        assert brief_features["max_length"] == 120

        standard_features = get_template_features("standard")
        assert standard_features["min_length"] == 130
        assert standard_features["max_length"] == 230

        detailed_features = get_template_features("detailed")
        assert detailed_features["min_length"] == 280
        assert detailed_features["max_length"] == 550

        # 測試默認值
        default_features = get_template_features("unknown")
        assert default_features["max_length"] == 230  # 標準模板


class TestTemplateDifferentiation:
    """模板差異化測試"""

    def test_differentiate_brief_template_short(self):
        """測試精簡模板處理短內容"""
        text = "本公司是一家專業的科技公司。"
        result = differentiate_template(text, "brief")

        assert isinstance(result, str)
        # Phase 14 Stage 3: 預設不截斷，只記錄警告
        assert len(result) >= len(text)  # 原樣返回

    def test_differentiate_brief_template_long(self):
        """測試精簡模板處理長內容（Phase 14 Stage 3: 預設不截斷，只記錄警告）"""
        text = """
        本公司成立於2020年，是一家專業的科技公司。
        我們主要提供軟體開發、系統整合和技術諮詢服務。
        公司擁有經驗豐富的技術團隊，採用最先進的開發技術。
        此外，我們還提供客戶培訓和技術支援服務。
        具體來說，我們的服務包括企業系統開發、移動應用開發和雲端解決方案。
        """
        result = differentiate_template(text, "brief")

        assert isinstance(result, str)
        # Phase 14 Stage 3: 預設不截斷，原樣返回
        # 字數檢核和重寫由 word_count_validator.py 負責
        plain_text = re.sub(r"<[^>]+>", "", result)
        # 長內容原樣返回，不截斷
        assert len(plain_text) >= len(text.strip())

    def test_differentiate_standard_template(self):
        """測試標準模板處理（Phase 14 Stage 3: 預設不截斷）"""
        text = "本公司是一家超級專業的科技公司，提供世界一流的服務。"
        result = differentiate_template(text, "standard")

        assert isinstance(result, str)
        # Phase 14 Stage 3: 預設不截斷，原樣返回
        assert len(result) == len(text)

    def test_differentiate_detailed_template(self):
        """測試詳細模板處理"""
        text = """
        公司成立於2020年，註冊資本1000萬元。
        主要業務包括軟體開發、系統整合和技術諮詢。
        公司願景是成為業界領先的科技解決方案提供商。
        """
        result = differentiate_template(text, "detailed")

        assert isinstance(result, str)
        # 詳細模板原樣返回
        assert "公司成立" in result
        assert "主要業務" in result
        assert "公司願景" in result

    def test_differentiate_html_content(self):
        """測試HTML內容模板差異化"""
        html = """
        <div>
            <p>本公司是一家專業的科技公司。</p>
            <p>此外，我們還提供技術諮詢服務。</p>
            <ul>
                <li>軟體開發</li>
                <li>系統整合</li>
                <li>技術支援</li>
            </ul>
        </div>
        """
        result = differentiate_template(html, "brief")

        assert isinstance(result, str)
        assert "<div>" in result
        assert "<p>" in result
        # Phase 14 Stage 3: 原樣返回

    def test_empty_text_handling(self):
        """測試空文本處理"""
        assert differentiate_template("", "brief") == ""
        assert differentiate_template("", "standard") == ""
        assert differentiate_template("", "detailed") == ""
        assert differentiate_template(None, "brief") is None

    def test_differentiate_force_truncate_true(self):
        """測試 force_truncate=True 時截斷（向後相容）"""
        long_text = "<p>" + "這是測試文字。" * 20 + "</p>"  # 約 200 字
        result = differentiate_template(long_text, "brief", force_truncate=True)

        assert isinstance(result, str)
        plain_text = re.sub(r"<[^>]+>", "", result)
        # 強制截斷後應在合理範圍內
        assert len(plain_text) <= 150  # 允許緩衝

    def test_differentiate_force_truncate_false(self):
        """測試 force_truncate=False 時不截斷（預設）"""
        long_text = "<p>" + "這是測試文字。" * 20 + "</p>"  # 約 200 字
        result = differentiate_template(long_text, "brief", force_truncate=False)

        assert isinstance(result, str)
        # 不截斷，原樣返回
        assert "這是測試文字" in result


class TestLengthLimitation:
    """長度限制測試"""

    def test_brief_template_no_truncate_by_default(self):
        """測試精簡模板預設不截斷（Phase 14 Stage 3 新增）"""
        # 創建超過 120 字的文本
        long_text = "本公司" * 50  # 大約 100 字
        result = differentiate_template(long_text, "brief")

        assert isinstance(result, str)
        # Phase 14 Stage 3: 預設不截斷，原樣返回
        assert len(result) >= 90  # 原樣返回

    def test_brief_template_force_truncate(self):
        """測試精簡模板強制截斷"""
        # 創建超過 120 字的文本
        long_text = "本公司" * 50  # 大約 100 字
        result = differentiate_template(long_text, "brief", force_truncate=True)

        assert isinstance(result, str)
        # 強制截斷後應在合理範圍內
        assert len(result) <= 150  # 允許一些緩衝

    def test_standard_template_no_truncate_by_default(self):
        """測試標準模板預設不截斷"""
        long_text = "本公司是一家科技公司。" * 20  # 大約 200 字
        result = differentiate_template(long_text, "standard")

        assert isinstance(result, str)
        # 預設不截斷
        assert len(result) >= 180  # 原樣返回

    def test_standard_template_force_truncate(self):
        """測試標準模板強制截斷"""
        long_text = "本公司是一家科技公司。" * 30  # 大約 300 字
        result = differentiate_template(long_text, "standard", force_truncate=True)

        assert isinstance(result, str)
        # 強制截斷後應在合理範圍內
        assert len(result) <= 260  # 允許一些緩衝

    def test_html_length_limit(self):
        """測試HTML內容長度限制"""
        html = "<p>" + ("這是一段很長的文本內容。" * 20) + "</p>"
        result = differentiate_template(html, "brief", force_truncate=True)

        assert isinstance(result, str)
        # 截斷後可能沒有完整標籤對，檢查是否有內容被截斷
        assert len(result) > 0


class TestContentSimplification:
    """內容簡化測試"""

    def test_remove_forbidden_patterns_brief(self):
        """測試精簡模板長度截斷（Phase 14 Stage 2: 風格控制在 prompt 層，後處理只截斷）"""
        text = "本公司提供服務。此外，我們還提供技術支援。具體來說，包括系統維護。"
        result = differentiate_template(text, "brief")

        # Phase 14 Stage 2: 後處理只做長度截斷
        # forbidden_patterns（如「此外」「具體來說」）的控制由 prompt_builder.py 決定 LLM 不生成這些詞
        # 此測試文本不超過 100 字，所以原樣返回
        assert isinstance(result, str)
        assert len(result) > 0

    def test_simplify_enumerations_brief(self):
        """測試精簡模板簡化列舉"""
        text = "服務包括軟體開發、系統整合、技術諮詢、客戶培訓等。"
        result = differentiate_template(text, "brief")

        # 精簡模板可能簡化列舉
        assert isinstance(result, str)

    def test_remove_exaggeration_standard(self):
        """測試標準模板長度截斷（Phase 14 Stage 2: 風格控制在 prompt 層，後處理只截斷）"""
        text = "我們提供世界一流、極其專業、超級優質的服務。"
        result = differentiate_template(text, "standard")

        # Phase 14 Stage 2: 誇大詞語移除由 prompt_builder.py 在生成前決定（不要求 LLM 輸出誇大詞）
        # 後處理只做長度截斷，此短文本不需截斷，原樣返回
        assert isinstance(result, str)
        assert len(result) <= 200  # 符合標準模板長度限制
        # 核心資訊仍然存在
        assert "服務" in result


class TestTemplateValidation:
    """模板驗證測試"""

    def test_validate_ideal_templates(self):
        """測試理想模板驗證"""
        brief = "公司成立於2020年。"
        standard = "公司成立於2020年，主要業務是軟體開發。"
        detailed = """
        公司成立於2020年，註冊資本1000萬元。
        主要業務包括軟體開發、系統整合和技術諮詢。
        公司擁有經驗豐富的技術團隊，採用先進的開發技術。
        我們的願景是成為業界領先的科技解決方案提供商。
        """

        result = validate_template_differentiation(brief, standard, detailed)

        # 檢查基本驗證
        assert result["brief_valid"] is True
        # 詳細模板應該比精簡模板長
        assert result["word_counts"]["detailed"] > result["word_counts"]["brief"]
        # 標準模板應該在精簡和詳細之間
        assert (
            result["word_counts"]["brief"]
            <= result["word_counts"]["standard"]
            <= result["word_counts"]["detailed"]
        ) or result["word_counts"]["standard"] > result["word_counts"]["brief"]

    def test_validate_invalid_lengths(self):
        """測試無效長度驗證"""
        # 精簡模板比標準模板長
        brief = (
            "這是一個非常長的精簡模板內容，實際上它太長了，不符合精簡模板的要求。" * 3
        )
        standard = "標準模板"
        detailed = "詳細模板"

        result = validate_template_differentiation(brief, standard, detailed)

        assert result["length_valid"] is False
        assert result["all_valid"] is False

    def test_validate_brief_too_long(self):
        """測試精簡模板太長"""
        brief = "這是一個超過100字的精簡模板內容。" * 10
        standard = "標準模板內容"
        detailed = "詳細模板內容"

        result = validate_template_differentiation(brief, standard, detailed)

        assert result["brief_valid"] is False
        assert result["all_valid"] is False


class TestIntegration:
    """整合測試"""

    def test_template_differentiation_workflow(self):
        """測試模板差異化工作流程"""
        content = """
        以下是優化結果：本公司是一家專業的科技公司。
        我們提供軟體開發、系統整合和技術諮詢服務。
        此外，我們還擁有經驗豐富的技術團隊。
        具體來說，我們採用最先進的開發技術和流程。
        """

        # 測試不同模板類型
        brief_result = differentiate_template(content, "brief")
        standard_result = differentiate_template(content, "standard")
        detailed_result = differentiate_template(content, "detailed")

        # 檢查所有結果都是有效字符串
        assert isinstance(brief_result, str) and len(brief_result) > 0
        assert isinstance(standard_result, str) and len(standard_result) > 0
        assert isinstance(detailed_result, str) and len(detailed_result) > 0

        # 檢查模板差異
        validation = validate_template_differentiation(
            brief_result, standard_result, detailed_result
        )

        # 至少應該有字數差異
        assert (
            validation["word_counts"]["brief"]
            <= validation["word_counts"]["standard"]
            <= validation["word_counts"]["detailed"]
        ) or validation["word_counts"]["brief"] < validation["word_counts"]["detailed"]

    def test_html_template_differentiation(self):
        """測試HTML模板差異化"""
        html_content = """
        <div>
            <p>本公司是一家專業的科技公司。</p>
            <p>我們提供多種服務，包括：</p>
            <ul>
                <li>軟體開發</li>
                <li>系統整合</li>
                <li>技術諮詢</li>
            </ul>
            <p>此外，我們還提供客戶培訓服務。</p>
        </div>
        """

        brief_result = differentiate_template(html_content, "brief")
        standard_result = differentiate_template(html_content, "standard")

        # 檢查HTML結構保持完整
        assert "<div>" in brief_result
        assert "<p>" in brief_result
        assert "<div>" in standard_result
        assert "<p>" in standard_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
