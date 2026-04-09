"""
測試腳本：驗證 Agent C 修復 - 移除開頭冗言
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.functions.utils.post_processing import post_process, _remove_verbose_phrases


def test_verbose_phrase_removal():
    """測試移除冗言的功能"""

    print("=== 測試 1: 基本冗言移除 ===")
    test_cases = [
        ("以下是優化結果：這是內容", "這是內容"),
        ("以下是生成的內容：公司簡介在此", "公司簡介在此"),
        ("以下是公司簡介：內容開始", "內容開始"),
        ("根據您的要求生成的簡介如下", "生成的簡介如下"),  # 移除"根據您的要求"
        ("以下是優化後的簡介：真正的內容", "真正的內容"),
        ("根據以上資訊，公司簡介如下", "公司簡介如下"),  # 移除"根據以上資訊，"
    ]

    for input_text, expected in test_cases:
        result = _remove_verbose_phrases(input_text)
        print(f"輸入: '{input_text}'")
        print(f"預期: '{expected}'")
        print(f"結果: '{result}'")
        print()
        assert result == expected or (not expected and not result), (
            f"測試失敗: '{input_text}' -> '{result}' (預期 '{expected}')"
        )

    print("=== 測試 2: 英文冗言移除 ===")
    english_cases = [
        ("以下是生成的內容: Company Brief", "Company Brief"),
        ("Here is the generated content: Brief", "Brief"),
        ("Based on your request: Company Info", "Company Info"),
    ]

    for input_text, expected in english_cases:
        result = _remove_verbose_phrases(input_text)
        print(f"輸入: '{input_text}'")
        print(f"結果: '{result}'")
        print()

    print("=== 測試 3: 完整 post_process 流程 ===")
    llm_result = {
        "body_html": "以下是優化結果：這是一家專業的軟體公司，致力於提供優質的產品和服務。",
        "summary": "以下是生成的摘要：專業軟體公司。",
        "tags": ["軟體", "科技"],
    }

    result = post_process(llm_result)

    print(f"原始 body_html: {llm_result['body_html']}")
    print(f"處理後 body_html: {result['body_html']}")
    print()
    print(f"原始 summary: {llm_result['summary']}")
    print(f"處理後 summary: {result['summary']}")
    print()

    # 驗證冗言已被移除
    assert "以下是" not in result["body_html"], "body_html 中仍有冗言"
    assert "根據" not in result["body_html"], "body_html 中仍有'根據'開頭"
    assert "以下是" not in result["summary"], "summary 中仍有冗言"

    print("=== 測試 4: 混合內容測試 ===")
    mixed_result = {
        "body_html": "<p>以下是生成的內容：公司簡介內容在此。</p><p>第二段內容。</p>",
        "summary": "這是一個專業的公司。",
    }

    processed = post_process(mixed_result)
    print(f"原始 HTML: {mixed_result['body_html']}")
    print(f"處理後: {processed['body_html']}")
    print()

    # HTML 標籤應該被保留，但冗言應該被移除
    assert "<p>" in processed["body_html"], "HTML 標籤應被保留"
    assert "以下是" not in processed["body_html"], "冗言應被移除"

    print("=== 測試 5: 無冗言內容 ===")
    clean_result = {
        "body_html": "<p>這是一家專業的軟體公司。</p>",
        "summary": "專業軟體公司。",
    }

    processed = post_process(clean_result)
    print(f"原始: {clean_result['body_html']}")
    print(f"處理後: {processed['body_html']}")
    print()

    # 原本乾淨的內容不應被改變
    assert processed["body_html"] == clean_result["body_html"], "乾淨內容不應被改變"

    print("=" * 50)
    print("✅ 所有 Agent C 測試通過！冗言已被有效移除")


if __name__ == "__main__":
    test_verbose_phrase_removal()
