"""
Phase 14 Stage 2: 模板差異化修復整合測試

測試目標:
1. 驗證 optimization_mode 參數正確傳遞到各層
2. 驗證 prompt_builder.py 根據模板類型生成不同的提示詞
3. 驗證三個模板的 Prompt 內容有明顯差異
4. 驗證 template_differentiator.py 的截斷功能正常
5. 驗證整體流程參數傳遞正確

注意：這些是「不需要實際呼叫 LLM」的單元/整合測試，
      驗證參數傳遞與 Prompt 生成的正確性。
"""

import pytest
import sys
import os
import re

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.functions.utils.prompt_builder import (
    build_generate_prompt,
    TEMPLATE_DESCRIPTIONS,
)
from src.functions.utils.template_differentiator import (
    differentiate_template,
    TEMPLATE_FEATURES,
    BRIEF_TEMPLATE_FEATURES,
    STANDARD_TEMPLATE_FEATURES,
    DETAILED_TEMPLATE_FEATURES,
)


# ===== 1. Prompt Builder 模板差異化測試 =====


class TestPromptBuilderTemplateDifferentiation:
    """測試 prompt_builder.py 的模板差異化功能"""

    def test_template_descriptions_exist(self):
        """測試三個模板的描述都存在"""
        assert "concise" in TEMPLATE_DESCRIPTIONS
        assert "standard" in TEMPLATE_DESCRIPTIONS
        assert "detailed" in TEMPLATE_DESCRIPTIONS

    def test_concise_template_description_is_defined(self):
        """測試精簡模板描述已定義"""
        desc = TEMPLATE_DESCRIPTIONS["concise"]
        assert "name" in desc
        assert "length_guide" in desc
        assert "content_guide" in desc
        assert "精簡" in desc["name"] or "concise" in desc["name"].lower()

    def test_standard_template_description_is_defined(self):
        """測試標準模板描述已定義"""
        desc = TEMPLATE_DESCRIPTIONS["standard"]
        assert "name" in desc
        assert "length_guide" in desc
        assert "content_guide" in desc

    def test_detailed_template_description_is_defined(self):
        """測試詳細模板描述已定義"""
        desc = TEMPLATE_DESCRIPTIONS["detailed"]
        assert "name" in desc
        assert "length_guide" in desc
        assert "content_guide" in desc
        assert "詳細" in desc["name"] or "detailed" in desc["name"].lower()

    def test_concise_prompt_contains_template_info(self):
        """測試精簡模板的 prompt 包含模板資訊"""
        prompt = build_generate_prompt(
            organ="測試公司",
            optimization_mode="concise",
        )
        # 應該包含模板名稱或模式
        assert "精簡" in prompt or "concise" in prompt.lower()
        # 應該包含新的字數要求 (40-120)
        assert "40" in prompt and "120" in prompt

    def test_standard_prompt_contains_template_info(self):
        """測試標準模板的 prompt 包含模板資訊"""
        prompt = build_generate_prompt(
            organ="測試公司",
            optimization_mode="standard",
        )
        # 應該包含標準模式標識
        assert "標準" in prompt or "standard" in prompt.lower()

    def test_detailed_prompt_contains_template_info(self):
        """測試詳細模板的 prompt 包含模板資訊"""
        prompt = build_generate_prompt(
            organ="測試公司",
            optimization_mode="detailed",
        )
        # 應該包含詳細模式標識
        assert "詳細" in prompt or "detailed" in prompt.lower()
        # 詳細模板應該有新的字數要求 (280-550)
        assert "280" in prompt and "550" in prompt

    def test_three_prompts_are_different(self):
        """測試三個模板生成的 Prompt 互不相同"""
        concise_prompt = build_generate_prompt(
            organ="測試公司", optimization_mode="concise"
        )
        standard_prompt = build_generate_prompt(
            organ="測試公司", optimization_mode="standard"
        )
        detailed_prompt = build_generate_prompt(
            organ="測試公司", optimization_mode="detailed"
        )

        # 三個 Prompt 應該不同
        assert concise_prompt != standard_prompt
        assert standard_prompt != detailed_prompt
        assert concise_prompt != detailed_prompt

    def test_concise_prompt_is_shorter_than_detailed(self):
        """測試精簡模板的 prompt 要求字數較少（指導詞更簡短）"""
        concise_prompt = build_generate_prompt(
            organ="測試公司", optimization_mode="concise"
        )
        detailed_prompt = build_generate_prompt(
            organ="測試公司", optimization_mode="detailed"
        )

        # 詳細模板的 prompt 通常更長，因為有更多要求
        assert len(detailed_prompt) >= len(concise_prompt)

    def test_default_mode_when_no_optimization_mode(self):
        """測試沒有指定 optimization_mode 時使用預設標準模式"""
        prompt_no_mode = build_generate_prompt(organ="測試公司")
        prompt_standard = build_generate_prompt(
            organ="測試公司", optimization_mode="standard"
        )

        # 無模式和標準模式的 prompt 應該包含相似的標準模式信息
        assert "標準" in prompt_no_mode

    def test_invalid_optimization_mode_falls_back_to_standard(self):
        """測試無效的 optimization_mode 回退到標準模式"""
        prompt = build_generate_prompt(
            organ="測試公司", optimization_mode="invalid_mode"
        )
        # 應該回退到標準模式
        assert "標準" in prompt

    def test_optimization_mode_with_word_limit(self):
        """測試 optimization_mode 與 word_limit 同時使用"""
        prompt = build_generate_prompt(
            organ="測試公司",
            optimization_mode="concise",
            word_limit=100,
        )
        # 應該包含模板資訊
        assert "精簡" in prompt
        # 也應該包含字數限制
        assert "100" in prompt

    def test_optimization_mode_with_required_fields(self):
        """測試 optimization_mode 與必要欄位一起使用"""
        prompt = build_generate_prompt(
            organ="測試公司",
            optimization_mode="detailed",
            capital=50000000,  # 5000萬
            employees=100,
            founded_year=2015,
        )
        # 應該包含詳細模板資訊
        assert "詳細" in prompt
        # 應該包含必要欄位
        assert "5000" in prompt or "5,000" in prompt or "500" in prompt
        assert "100" in prompt
        assert "2015" in prompt


# ===== 2. 參數傳遞驗證測試 =====


class TestParameterPassingChain:
    """測試參數傳遞鏈是否正確"""

    def test_generate_brief_accepts_optimization_mode(self):
        """測試 generate_brief 函數接受 optimization_mode 參數（通過原始碼分析）"""
        # 由於 langgraph 可能不在測試環境中，通過原始碼分析驗證
        import ast
        import os

        generate_brief_path = os.path.join(
            os.path.dirname(__file__), "../src/functions/utils/generate_brief.py"
        )

        with open(generate_brief_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # 驗證 optimization_mode 在源碼中存在
        assert "optimization_mode" in source_code, (
            "generate_brief.py 應包含 optimization_mode 參數"
        )
        # 驗證 optimization_mode 被傳遞給 generate_company_brief
        assert "optimization_mode=optimization_mode" in source_code, (
            "generate_brief.py 應將 optimization_mode 傳遞給 generate_company_brief"
        )

    def test_state_has_optimization_mode_field(self):
        """測試狀態定義包含 optimization_mode 欄位"""
        from src.langgraph_state.state import CompanyBriefState, create_initial_state

        # 驗證 CompanyBriefState 定義中有 optimization_mode
        state_fields = CompanyBriefState.__annotations__
        assert "optimization_mode" in state_fields, (
            "CompanyBriefState 應包含 optimization_mode 欄位"
        )

    def test_create_initial_state_accepts_optimization_mode(self):
        """測試 create_initial_state 接受 optimization_mode 參數"""
        from src.langgraph_state.state import create_initial_state

        # 建立包含 optimization_mode 的初始狀態
        state = create_initial_state(
            organ="測試公司",
            optimization_mode="concise",
        )

        assert state["optimization_mode"] == "concise"

    def test_create_initial_state_default_optimization_mode_is_none(self):
        """測試 create_initial_state 預設 optimization_mode 為 None"""
        from src.langgraph_state.state import create_initial_state

        state = create_initial_state(organ="測試公司")
        assert state["optimization_mode"] is None

    def test_create_initial_state_with_all_modes(self):
        """測試 create_initial_state 接受所有三種模板類型"""
        from src.langgraph_state.state import create_initial_state

        for mode in ["concise", "standard", "detailed"]:
            state = create_initial_state(
                organ="測試公司",
                optimization_mode=mode,
            )
            assert state["optimization_mode"] == mode, (
                f"create_initial_state 應支援模板類型 '{mode}'"
            )

    def test_company_brief_graph_accepts_optimization_mode(self):
        """測試 CompanyBriefGraph.invoke 接受 optimization_mode 參數（通過原始碼分析）"""
        import os

        graph_path = os.path.join(
            os.path.dirname(__file__), "../src/langgraph_state/company_brief_graph.py"
        )

        with open(graph_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # 驗證 invoke 方法中有 optimization_mode 參數
        assert "optimization_mode" in source_code, (
            "company_brief_graph.py 應包含 optimization_mode 參數"
        )
        # 驗證 optimization_mode 傳遞給 create_initial_state
        assert (
            "optimization_mode," in source_code or "optimization_mode)" in source_code
        ), "company_brief_graph.py 應將 optimization_mode 傳遞給 create_initial_state"

    def test_generate_company_brief_accepts_optimization_mode(self):
        """測試 generate_company_brief 函數簽名含 optimization_mode（通過原始碼分析）"""
        import os

        graph_path = os.path.join(
            os.path.dirname(__file__), "../src/langgraph_state/company_brief_graph.py"
        )

        with open(graph_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # 驗證 generate_company_brief 函數接受 optimization_mode
        # 找到函數定義並確認 optimization_mode 在參數列表中
        import re

        func_pattern = r"def generate_company_brief\([^)]+\)"
        matches = re.findall(func_pattern, source_code, re.DOTALL)
        assert matches, "應找到 generate_company_brief 函數定義"
        assert "optimization_mode" in matches[0], (
            "generate_company_brief 函數應包含 optimization_mode 參數"
        )


# ===== 3. Template Differentiator 截斷功能測試 =====


class TestTemplateDifferentiatorTruncation:
    """測試 template_differentiator.py 的截斷功能"""

    def test_brief_truncates_to_100_chars(self):
        """測試精簡模板截斷到 120 字（使用 force_truncate=True）"""
        # Phase 14 Stage 3: 預設不截斷，需要使用 force_truncate=True
        long_content = "<p>" + ("這是一段很長的文字內容，" * 20) + "</p>"
        result = differentiate_template(
            long_content, template_type="brief", force_truncate=True
        )

        # 移除 HTML 標籤計算純文字長度
        plain_text = re.sub(r"<[^>]+>", "", result)
        assert len(plain_text) <= BRIEF_TEMPLATE_FEATURES["max_length"] + 5, (
            f"精簡模板應截斷到 {BRIEF_TEMPLATE_FEATURES['max_length']} 字以內，"
            f"實際: {len(plain_text)} 字"
        )

    def test_standard_truncates_to_200_chars(self):
        """測試標準模板截斷到 230 字（使用 force_truncate=True）"""
        long_content = "<p>" + ("這是一段很長的標準文字內容，" * 20) + "</p>"
        result = differentiate_template(
            long_content, template_type="standard", force_truncate=True
        )

        plain_text = re.sub(r"<[^>]+>", "", result)
        assert len(plain_text) <= STANDARD_TEMPLATE_FEATURES["max_length"] + 5, (
            f"標準模板應截斷到 {STANDARD_TEMPLATE_FEATURES['max_length']} 字以內，"
            f"實際: {len(plain_text)} 字"
        )

    def test_detailed_truncates_to_500_chars(self):
        """測試詳細模板截斷到 550 字（使用 force_truncate=True）"""
        long_content = "<p>" + ("這是一段很長的詳細文字內容，" * 50) + "</p>"
        result = differentiate_template(
            long_content, template_type="detailed", force_truncate=True
        )

        plain_text = re.sub(r"<[^>]+>", "", result)
        assert len(plain_text) <= DETAILED_TEMPLATE_FEATURES["max_length"] + 5, (
            f"詳細模板應截斷到 {DETAILED_TEMPLATE_FEATURES['max_length']} 字以內，"
            f"實際: {len(plain_text)} 字"
        )

    def test_standard_truncates_to_200_chars(self):
        """測試標準模板截斷到 230 字（使用 force_truncate=True）"""
        # Phase 14 Stage 3: 預設不截斷，需要使用 force_truncate=True
        long_content = "<p>" + "這是一段很長的標準文字內容，" * 20 + "</p>"
        result = differentiate_template(
            long_content, template_type="standard", force_truncate=True
        )

        plain_text = re.sub(r"<[^>]+>", "", result)
        assert len(plain_text) <= STANDARD_TEMPLATE_FEATURES["max_length"] + 5, (
            f"標準模板應截斷到 {STANDARD_TEMPLATE_FEATURES['max_length']} 字以內，"
            f"實際: {len(plain_text)} 字"
        )

    def test_detailed_truncates_to_500_chars(self):
        """測試詳細模板截斷到 550 字（使用 force_truncate=True）"""
        long_content = "<p>" + "這是一段很長的詳細文字內容，" * 50 + "</p>"
        result = differentiate_template(
            long_content, template_type="detailed", force_truncate=True
        )

        plain_text = re.sub(r"<[^>]+>", "", result)
        assert len(plain_text) <= DETAILED_TEMPLATE_FEATURES["max_length"] + 5, (
            f"詳細模板應截斷到 {DETAILED_TEMPLATE_FEATURES['max_length']} 字以內，"
            f"實際: {len(plain_text)} 字"
        )

    def test_short_content_not_truncated(self):
        """測試短內容不會被截斷"""
        short_content = "<p>這是短內容。</p>"
        for template_type in ["brief", "standard", "detailed"]:
            result = differentiate_template(short_content, template_type=template_type)
            # 短內容應該原樣返回（或至少不被截短）
            assert "短內容" in result, f"模板 {template_type} 不應截斷短內容"

    def test_empty_content_returns_empty(self):
        """測試空內容返回空值"""
        result = differentiate_template("", template_type="brief")
        assert result == "" or result is None

    def test_none_content_returns_none(self):
        """測試 None 內容返回 None"""
        result = differentiate_template(None, template_type="standard")
        assert result is None


# ===== 4. Prompt 內容差異性驗證測試 =====


class TestPromptContentDifference:
    """測試三個模板的 Prompt 內容差異"""

    def test_concise_prompt_emphasizes_brevity(self):
        """測試精簡模板 Prompt 強調簡潔"""
        prompt = build_generate_prompt(organ="測試公司", optimization_mode="concise")
        # 應該含有簡潔相關關鍵字
        concise_keywords = ["精簡", "極簡", "簡潔", "50", "100", "核心"]
        found_keywords = [kw for kw in concise_keywords if kw in prompt]
        assert len(found_keywords) >= 2, (
            f"精簡模板 Prompt 應包含簡潔相關關鍵字，找到: {found_keywords}"
        )

    def test_detailed_prompt_emphasizes_completeness(self):
        """測試詳細模板 Prompt 強調完整性"""
        prompt = build_generate_prompt(organ="測試公司", optimization_mode="detailed")
        # 應該含有詳細相關關鍵字
        detailed_keywords = ["詳細", "完整", "包含", "300", "500", "願景"]
        found_keywords = [kw for kw in detailed_keywords if kw in prompt]
        assert len(found_keywords) >= 2, (
            f"詳細模板 Prompt 應包含詳細相關關鍵字，找到: {found_keywords}"
        )

    def test_concise_content_guide_is_simpler_than_detailed(self):
        """測試精簡模板的 content_guide 比詳細模板更簡短"""
        concise_guide = TEMPLATE_DESCRIPTIONS["concise"]["content_guide"]
        detailed_guide = TEMPLATE_DESCRIPTIONS["detailed"]["content_guide"]

        # 詳細模板的 content_guide 應該更長（因為有更多要求）
        assert len(detailed_guide) > len(concise_guide), (
            "詳細模板的 content_guide 應該比精簡模板更長"
        )

    def test_template_length_guides_show_progression(self):
        """測試三個模板的長度指引呈遞增"""
        concise_guide = TEMPLATE_DESCRIPTIONS["concise"]["length_guide"]
        standard_guide = TEMPLATE_DESCRIPTIONS["standard"]["length_guide"]
        detailed_guide = TEMPLATE_DESCRIPTIONS["detailed"]["length_guide"]

        # 從 length_guide 提取數字確認遞增
        def extract_max_number(guide):
            numbers = re.findall(r"\d+", guide)
            return max(int(n) for n in numbers) if numbers else 0

        concise_max = extract_max_number(concise_guide)
        standard_max = extract_max_number(standard_guide)
        detailed_max = extract_max_number(detailed_guide)

        assert concise_max < standard_max, (
            f"精簡模板最大字數 ({concise_max}) 應小於標準模板 ({standard_max})"
        )
        assert standard_max < detailed_max, (
            f"標準模板最大字數 ({standard_max}) 應小於詳細模板 ({detailed_max})"
        )


# ===== 5. 模擬 LLM 輸出的後處理整合測試 =====


class TestSimulatedTemplateProcessing:
    """使用模擬的 LLM 輸出測試後處理流程"""

    def test_concise_simulated_output_is_within_limit(self):
        """測試精簡模板模擬輸出在長度限制內"""
        # 模擬精簡 LLM 輸出（80字）
        simulated_concise = "<p>測試科技股份有限公司專注於軟體開發，提供企業數位轉型服務，以創新技術協助客戶提升競爭力。</p>"
        result = differentiate_template(simulated_concise, template_type="brief")
        plain = re.sub(r"<[^>]+>", "", result)
        assert len(plain) <= BRIEF_TEMPLATE_FEATURES["max_length"]

    def test_standard_simulated_output_is_within_limit(self):
        """測試標準模板模擬輸出在長度限制內"""
        # 模擬標準 LLM 輸出（180字）
        simulated_standard = (
            "<p>測試科技股份有限公司成立於2010年，專注於企業軟體開發與系統整合服務。"
            "公司旗下擁有專業的研發團隊，致力於提供高品質的技術解決方案。</p>"
            "<p>公司主要服務包括：企業資源規劃系統、客戶關係管理系統、電子商務平台等。"
            "多年來服務超過500家企業客戶，在業界建立了良好口碑，持續推動台灣數位轉型。</p>"
        )
        result = differentiate_template(simulated_standard, template_type="standard")
        plain = re.sub(r"<[^>]+>", "", result)
        assert len(plain) <= STANDARD_TEMPLATE_FEATURES["max_length"]

    def test_detailed_simulated_output_preserves_content(self):
        """測試詳細模板模擬輸出保留豐富內容"""
        # 模擬詳細 LLM 輸出（350字）
        simulated_detailed = (
            "<p>測試科技股份有限公司成立於2010年，總部位於台北，是台灣領先的企業軟體解決方案提供商。</p>"
            "<p>公司創立之初，以「科技驅動業務成長」為核心理念，致力於協助台灣中小企業完成數位轉型。</p>"
            "<p>主要服務項目包括：企業資源規劃（ERP）系統、客戶關係管理（CRM）平台、電子商務解決方案、"
            "雲端基礎設施建置及資安防護服務，提供從規劃、開發到維護的一站式服務。</p>"
            "<p>公司目前擁有120名專業人員，其中技術團隊佔70%，多次獲得政府及業界頒發的優良廠商認證。</p>"
            "<p>展望未來，公司將持續深耕人工智慧與大數據應用，協助客戶在瞬息萬變的市場中保持競爭優勢。</p>"
        )
        result = differentiate_template(simulated_detailed, template_type="detailed")
        plain = re.sub(r"<[^>]+>", "", result)

        # 詳細模板應保留更多內容
        assert len(plain) >= 100, "詳細模板輸出應保留足夠的內容"
        assert len(plain) <= DETAILED_TEMPLATE_FEATURES["max_length"]

    def test_post_process_with_optimization_mode(self):
        """測試 post_process 與模板類型整合"""
        from src.functions.utils.post_processing import post_process

        llm_result = {
            "body_html": "<p>測試科技公司是一家專業的科技企業，提供優質服務。</p>",
            "summary": "測試科技公司：專業科技企業",
            "tags": ["科技"],
        }

        # 測試三個模板的後處理
        for template_type in ["brief", "standard", "detailed"]:
            result = post_process(llm_result, template_type=template_type)
            assert "body_html" in result, f"模板 {template_type} 後處理應返回 body_html"
            assert result["body_html"], (
                f"模板 {template_type} 後處理 body_html 不應為空"
            )


# ===== 6. 向後相容性測試 =====


class TestBackwardCompatibility:
    """測試向後相容性：確保沒有 optimization_mode 時仍然正常運作"""

    def test_build_prompt_without_optimization_mode(self):
        """測試不提供 optimization_mode 時 build_generate_prompt 正常運作"""
        prompt = build_generate_prompt(organ="測試公司")
        assert prompt
        assert "測試公司" in prompt

    def test_differentiate_template_default_is_standard(self):
        """測試 differentiate_template 預設為 standard 模板"""
        content = "<p>測試內容。</p>"
        result = differentiate_template(content)
        # 應該正常執行，不報錯
        assert result

    def test_create_initial_state_without_optimization_mode(self):
        """測試不提供 optimization_mode 時 create_initial_state 正常運作"""
        from src.langgraph_state.state import create_initial_state

        state = create_initial_state(organ="測試公司")
        assert state["organ"] == "測試公司"
        assert state.get("optimization_mode") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
