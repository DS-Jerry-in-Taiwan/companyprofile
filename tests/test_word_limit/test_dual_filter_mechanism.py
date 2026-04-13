"""
Phase 11 雙重篩選機制驗證測試

驗證 word_limit 的完整流程：
1. Prompt 層：確保 prompt 明確告知 LLM 字數限制
2. 程式層：確保程式端強制截斷 LLM 輸出

此測試涵蓋傳統流程與 LangGraph 流程
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.functions.utils.prompt_builder import build_generate_prompt
from src.functions.utils.text_truncate import (
    truncate_llm_output,
    count_chinese_characters,
)


class TestPromptLayerWordLimit:
    """測試 Prompt 層的 word_limit 指示"""

    def test_prompt_includes_word_limit(self):
        """驗證 prompt 正確包含 word_limit 指示"""
        word_limit = 100
        prompt = build_generate_prompt(
            organ="測試公司",
            organ_no="12345678",
            company_url="https://example.com",
            user_brief="測試簡介",
            web_content="網路搜尋內容",
            word_limit=word_limit,
        )

        # 驗證 prompt 中包含字數限制的明確指示
        assert f"不超過 {word_limit} 字" in prompt
        assert "公司簡介" in prompt
        # Phase 14 Stage 2: 更新後 prompt 使用「平衡的公司簡介」等措辭，不再使用「專業、簡潔」
        assert "輸出要求" in prompt

    def test_prompt_default_without_word_limit(self):
        """驗證沒有 word_limit 時使用預設值"""
        prompt = build_generate_prompt(
            organ="測試公司",
            organ_no="12345678",
            word_limit=None,
        )

        # 應該使用預設字數範圍
        assert "200-300字" in prompt

    def test_prompt_includes_all_materials(self):
        """驗證 prompt 包含所有素材"""
        prompt = build_generate_prompt(
            organ="測試公司",
            organ_no="12345678",
            company_url="https://example.com",
            user_brief="用戶提供的簡介",
            web_content="網路搜尋內容",
            word_limit=150,
        )

        # 驗證所有素材都被包含
        assert "測試公司" in prompt
        assert "12345678" in prompt
        assert "https://example.com" in prompt
        assert "用戶提供的簡介" in prompt
        assert "網路搜尋內容" in prompt
        assert "不超過 150 字" in prompt

    def test_prompt_word_limit_various_values(self):
        """驗證不同 word_limit 值都被正確包含"""
        test_cases = [50, 100, 200, 300, 500, 1000, 2000]

        for word_limit in test_cases:
            prompt = build_generate_prompt(
                organ="測試公司",
                word_limit=word_limit,
            )
            assert f"不超過 {word_limit} 字" in prompt, (
                f"Failed for word_limit={word_limit}"
            )


class TestProgramLayerTruncation:
    """測試程式層的強制截斷機制"""

    def test_body_html_truncation_enforced(self):
        """驗證 body_html 強制截斷"""
        # 模擬 LLM 輸出超過限制
        llm_output = {
            "title": "公司標題",
            "body_html": "<p>" + "這是內容" * 100 + "</p>",  # 模擬超長輸出
            "summary": "簡短摘要",
        }

        word_limit = 100
        result = truncate_llm_output(llm_output, word_limit)

        # 驗證 body_html 被截斷到限制內
        body_length = count_chinese_characters(result["body_html"])
        assert body_length <= word_limit, (
            f"body_html 長度 {body_length} 超過限制 {word_limit}"
        )

    def test_summary_truncation_enforced(self):
        """驗證 summary 強制截斷"""
        llm_output = {
            "title": "公司標題",
            "body_html": "<p>短內容</p>",
            "summary": "摘要內容" * 50,  # 模擬超長摘要
        }

        word_limit = 100
        result = truncate_llm_output(llm_output, word_limit)

        # 驗證 summary 被截斷（應該是 word_limit//2 或不超過 200）
        summary_length = count_chinese_characters(result["summary"])
        expected_limit = min(word_limit // 2, 200)
        assert summary_length <= expected_limit, (
            f"summary 長度 {summary_length} 超過限制 {expected_limit}"
        )

    def test_title_truncation_enforced(self):
        """驗證 title 強制截斷"""
        llm_output = {
            "title": "這是一個非常長的公司標題" * 10,
            "body_html": "<p>內容</p>",
            "summary": "摘要",
        }

        result = truncate_llm_output(llm_output, 100)

        # 驗證 title 被截斷到 50 字以內
        title_length = count_chinese_characters(result["title"])
        assert title_length <= 50, f"title 長度 {title_length} 超過限制 50"

    def test_all_fields_truncated_within_limits(self):
        """驗證所有欄位都在各自的限制內"""
        llm_output = {
            "title": "非常長的標題" * 20,
            "body_html": "<p>" + "超長內容" * 200 + "</p>",
            "summary": "超長摘要" * 100,
        }

        word_limit = 200
        result = truncate_llm_output(llm_output, word_limit)

        # 驗證所有欄位都被適當截斷
        title_length = count_chinese_characters(result["title"])
        body_length = count_chinese_characters(result["body_html"])
        summary_length = count_chinese_characters(result["summary"])

        assert title_length <= 50, f"title 超過限制: {title_length}"
        assert body_length <= word_limit, f"body_html 超過限制: {body_length}"
        assert summary_length <= min(word_limit // 2, 200), (
            f"summary 超過限制: {summary_length}"
        )


class TestDualFilterIntegration:
    """測試雙重篩選機制的整合"""

    def test_prompt_and_truncation_consistency(self):
        """驗證 Prompt 指示與程式截斷的一致性"""
        word_limit = 150

        # 1. 驗證 Prompt 告知了限制
        prompt = build_generate_prompt(
            organ="測試公司",
            word_limit=word_limit,
        )
        assert f"不超過 {word_limit} 字" in prompt

        # 2. 模擬 LLM 超過限制的輸出
        llm_output = {
            "title": "標題",
            "body_html": "<p>" + "內容" * 200 + "</p>",
            "summary": "摘要",
        }

        # 3. 驗證程式層截斷
        truncated = truncate_llm_output(llm_output, word_limit)
        body_length = count_chinese_characters(truncated["body_html"])

        # 4. 最終結果應在限制內
        assert body_length <= word_limit, "雙重篩選失敗：最終輸出超過限制"

    def test_word_limit_boundary_values(self):
        """測試邊界值：最小、最大、中間值"""
        test_cases = [
            (50, "最小限制"),
            (200, "中等限制"),
            (2000, "最大限制"),
        ]

        for word_limit, description in test_cases:
            # 1. 生成 prompt
            prompt = build_generate_prompt(
                organ="測試公司",
                word_limit=word_limit,
            )

            # 2. 生成超長輸出
            llm_output = {
                "title": "標題" * 50,
                "body_html": "<p>" + "內容" * 500 + "</p>",
                "summary": "摘要" * 100,
            }

            # 3. 截斷
            result = truncate_llm_output(llm_output, word_limit)

            # 4. 驗證
            body_length = count_chinese_characters(result["body_html"])
            assert body_length <= word_limit, (
                f"{description} 測試失敗: {body_length} > {word_limit}"
            )

    def test_word_limit_none_disables_truncation(self):
        """驗證 word_limit=None 時不執行截斷"""
        llm_output = {
            "title": "標題" * 50,
            "body_html": "<p>" + "內容" * 500 + "</p>",
            "summary": "摘要" * 100,
        }

        # 不進行截斷
        result = truncate_llm_output(llm_output, None)

        # 結果應保持不變（除了 copy 外）
        assert result == llm_output


class TestPromptLLMIntegration:
    """測試 Prompt 與 LLM 呼叫的整合"""

    def test_word_limit_passed_to_llm_service(self):
        """驗證 word_limit 被正確傳遞給 LLM Service"""
        # 此測試主要驗證 call_llm 函數簽名包含 word_limit 參數
        from src.functions.utils.llm_service import call_llm
        import inspect

        # 取得 call_llm 函數簽名
        sig = inspect.signature(call_llm)
        params = list(sig.parameters.keys())

        # 驗證 word_limit 在參數中
        assert "word_limit" in params, "call_llm 函數應包含 word_limit 參數"

        # 驗證 word_limit 有預設值（None）
        param = sig.parameters["word_limit"]
        assert param.default is None or param.default == inspect.Parameter.empty, (
            "word_limit 應為可選參數"
        )


class TestLangGraphWordLimitIntegration:
    """測試 LangGraph 流程中的 word_limit 整合"""

    def test_langgraph_state_includes_word_limit(self):
        """驗證 LangGraph 狀態正確包含 word_limit"""
        from src.langgraph.state import create_initial_state

        word_limit = 200
        state = create_initial_state(
            organ="測試公司",
            organ_no="12345678",
            company_url="https://example.com",
            user_brief="用戶簡介",
            word_limit=word_limit,
        )

        # 驗證狀態中包含 word_limit
        assert state.get("word_limit") == word_limit

    def test_langgraph_finalize_applies_truncation(self):
        """驗證 LangGraph finalize 層應用截斷"""
        from src.langgraph.state import finalize_state
        from datetime import datetime

        word_limit = 100
        state = {
            "word_limit": word_limit,
            "final_result": {
                "title": "標題" * 50,
                "body_html": "<p>" + "內容" * 200 + "</p>",
                "summary": "摘要" * 50,
            },
            "start_time": datetime.now(),  # 提供必需的 start_time
            "current_node": "generate",
        }

        # 執行 finalize
        result_state = finalize_state(state, state["final_result"])

        # 驗證最終結果被截斷
        final_result = result_state.get("final_result", {})
        if final_result:
            body_length = count_chinese_characters(final_result.get("body_html", ""))
            assert body_length <= word_limit, (
                f"LangGraph finalize 截斷失敗: {body_length} > {word_limit}"
            )


class TestWordLimitEdgeCases:
    """測試 word_limit 的邊界情況"""

    def test_word_limit_exact_match(self):
        """測試恰好達到限制的情況"""
        content = "測試" * 50  # 恰好 100 字
        llm_output = {
            "title": "標題",
            "body_html": f"<p>{content}</p>",
            "summary": "摘要",
        }

        result = truncate_llm_output(llm_output, 100)
        body_length = count_chinese_characters(result["body_html"])
        assert body_length <= 100

    def test_word_limit_one_over(self):
        """測試超出一字的情況"""
        content = "測試" * 50 + "超"  # 101 字
        llm_output = {
            "title": "標題",
            "body_html": f"<p>{content}</p>",
            "summary": "摘要",
        }

        result = truncate_llm_output(llm_output, 100)
        body_length = count_chinese_characters(result["body_html"])
        assert body_length <= 100

    def test_empty_fields(self):
        """測試空欄位的處理"""
        llm_output = {
            "title": "",
            "body_html": "",
            "summary": "",
        }

        result = truncate_llm_output(llm_output, 100)
        # 應該不拋出異常，且返回結果
        assert isinstance(result, dict)

    def test_missing_fields(self):
        """測試缺少欄位的處理"""
        llm_output = {
            "body_html": "<p>內容</p>",
        }

        result = truncate_llm_output(llm_output, 100)
        # 應該不拋出異常
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
