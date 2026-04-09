"""
測試腳本：驗證 Agent B 修復 - 字數限制嚴格遵守
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.functions.utils.text_truncate import (
    truncate_text,
    truncate_llm_output,
    count_chinese_characters,
)


def test_word_limit_strictness():
    """測試字數限制的嚴格遵守"""

    print("=== 測試 1: 嚴格的 50 字限制 ===")
    long_text = "這是一段很長的文字。" * 15  # 這會產生 90 個字
    result = truncate_text(long_text, 50, preserve_html=False)
    actual_length = len(result)
    print(f"原始長度: {len(long_text)}")
    print(f"限制: 50")
    print(f"實際長度: {actual_length}")
    print(f"結果: {result}")
    print()
    assert actual_length <= 50, f"長度 {actual_length} 超出限制 50"

    print("=== 測試 2: HTML 段落截斷 ===")
    html_text = "<p>第一段內容。這是第二段。第三段的最後部分。</p><p>第四段開始。第五段的最後一句話。</p>"
    result = truncate_text(html_text, 30, preserve_html=True)
    actual_length = count_chinese_characters(result)
    print(f"原始 HTML: {html_text}")
    print(f"限制: 30")
    print(f"實際長度: {actual_length}")
    print(f"截斷結果: {result}")
    print()
    assert actual_length <= 30, f"長度 {actual_length} 超出限制 30"

    print("=== 測試 3: 自然邊界截斷 ===")
    # 測試是否在句號處截斷
    text_with_sentences = "這是第一句話。這是第二句話。這是第三句話。"
    result = truncate_text(text_with_sentences, 15, preserve_html=False)
    actual_length = len(result)
    print(f"原始: {text_with_sentences}")
    print(f"限制: 15")
    print(f"實際長度: {actual_length}")
    print(f"結果: '{result}'")
    print()
    # 應該在句號處截斷
    assert result.endswith("。") or len(result) <= 15, "未在自然邊界截斷"

    print("=== 測試 4: 完整 LLM 輸出截斷 ===")
    llm_output = {
        "title": "公司簡介標題",
        "body_html": "<p>這是一段很長的內容需要被嚴格截斷。" * 10 + "</p>",
        "summary": "這是一個很長的摘要需要被截斷。" * 5,
    }
    result = truncate_llm_output(llm_output, 50)

    body_length = count_chinese_characters(result["body_html"])
    summary_limit = min(50 // 2, 200)  # 25
    summary_length = count_chinese_characters(result["summary"])
    title_length = count_chinese_characters(result["title"])

    print(f"body_html 限制: 50, 實際: {body_length}")
    print(f"summary 限制: {summary_limit}, 實際: {summary_length}")
    print(f"title 限制: 50, 實際: {title_length}")
    print()

    assert body_length <= 50, f"body_html 超出限制: {body_length}"
    assert summary_length <= summary_limit, f"summary 超出限制: {summary_length}"
    assert title_length <= 50, f"title 超出限制: {title_length}"

    print("=== 測試 5: 多段落保留 ===")
    multi_para = "<p>第一段話。」</p><p>第二段話。</p><p>第三段話。</p>"
    result = truncate_text(multi_para, 25, preserve_html=True)
    actual_length = count_chinese_characters(result)
    print(f"原始: {multi_para}")
    print(f"限制: 25")
    print(f"實際長度: {actual_length}")
    print(f"結果: {result}")
    print()
    # 應該保留 <p> 標籤結構
    assert "<p>" in result, "未保留段落結構"

    print("=== 測試 6: 精確邊界測試 ===")
    # 測試極端情況：正好在邊界
    exact_boundary = "ABC。" * 20  # 60 characters
    result = truncate_text(exact_boundary, 20, preserve_html=False)
    actual_length = len(result)
    print(f"原始: {exact_boundary}")
    print(f"限制: 20")
    print(f"實際長度: {actual_length}")
    print(f"結果: '{result}'")
    print()
    assert actual_length <= 20, f"超出精確邊界: {actual_length}"

    print("=" * 50)
    print("✅ 所有 Agent B 測試通過！字數限制已嚴格遵守")


if __name__ == "__main__":
    test_word_limit_strictness()
