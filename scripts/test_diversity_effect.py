#!/usr/bin/env python3
"""
內容多樣化效果驗證腳本
驗證模板感消除和內容多樣化效果
"""

import sys
import os
import random

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.functions.utils.content_diversifier import (
    diversify_content,
    calculate_diversity_score,
    _remove_template_patterns,
)


def test_template_removal():
    """測試模板移除效果"""
    print("=" * 60)
    print("測試 1: 模板移除效果")
    print("=" * 60)

    test_cases = [
        ("以下是優化結果：公司成立於2020年。", "公司成立於2020年。"),
        ("根據您的要求，公司主要業務是軟體開發。", "公司主要業務是軟體開發。"),
        (
            "Here is the optimized result: Company founded in 2020.",
            "Company founded in 2020.",
        ),
    ]

    for input_text, expected in test_cases:
        result = _remove_template_patterns(input_text)
        print(f"輸入: {input_text}")
        print(f"輸出: {result}")
        print(f"預期: {expected}")
        print(f"匹配: {'✅' if result == expected else '❌'}")
        print("-" * 40)


def test_diversity_multiple_runs():
    """測試多次運行的多樣性"""
    print("\n" + "=" * 60)
    print("測試 2: 多次運行的多樣性")
    print("=" * 60)

    # 使用更豐富的測試內容
    test_content = """
    <p>以下是優化結果：本公司是一家非常專業的科技公司。</p>
    <p>我們提供世界一流的軟體開發和系統整合服務。</p>
    <p>此外，公司擁有經驗豐富的技術團隊，採用最先進的技術。</p>
    <p>具體來說，我們的服務包括企業系統開發、移動應用開發。</p>
    """

    print(f"原始內容:\n{test_content}")
    print("\n5次多樣化結果:")

    results = []
    for i in range(5):
        random.seed(i)  # 使用不同種子確保多樣性
        result = diversify_content(test_content)
        results.append(result)
        print(f"\n--- 第 {i + 1} 次 ---")
        print(result[:200] + "..." if len(result) > 200 else result)

    # 計算差異度
    print("\n" + "=" * 60)
    print("差異度分析:")
    print("=" * 60)

    diversity_scores = []
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            score = calculate_diversity_score(results[i], results[j])
            diversity_scores.append(score)
            print(f"結果 {i + 1} vs 結果 {j + 1}: 差異度 = {score:.2f}")

    avg_diversity = (
        sum(diversity_scores) / len(diversity_scores) if diversity_scores else 0
    )
    print(f"\n平均差異度: {avg_diversity:.2f}")
    print(f"是否 > 0.3: {'✅' if avg_diversity > 0.3 else '❌'}")


def test_real_world_scenarios():
    """測試真實場景"""
    print("\n" + "=" * 60)
    print("測試 3: 真實場景測試")
    print("=" * 60)

    scenarios = [
        {
            "name": "科技公司描述",
            "content": """
            <p>以下是優化結果：ABC科技有限公司成立於2018年。</p>
            <p>我們提供企業級軟體解決方案，包括ERP系統和CRM系統。</p>
            <p>此外，公司擁有50名員工，其中80%為技術人員。</p>
            """,
        },
        {
            "name": "顧問公司描述",
            "content": """
            <p>根據您的要求，XYZ顧問公司是一家專業的管理諮詢公司。</p>
            <p>我們提供戰略規劃、組織變革和流程優化服務。</p>
            <p>具體來說，我們採用國際最佳實踐方法論。</p>
            """,
        },
    ]

    for scenario in scenarios:
        print(f"\n📋 場景: {scenario['name']}")
        print(f"原始內容:\n{scenario['content']}")

        result = diversify_content(scenario["content"])
        print(f"\n多樣化後:\n{result}")

        # 檢查模板是否被移除
        has_template = any(
            [
                "以下是優化結果" in result,
                "根據您的要求" in result,
                "此外，" in result,
                "具體來說，" in result,
            ]
        )
        print(f"模板痕跡: {'❌ 仍有模板' if has_template else '✅ 已消除'}")
        print("-" * 40)


def test_integration_with_post_processing():
    """測試與後處理的整合"""
    print("\n" + "=" * 60)
    print("測試 4: 與後處理整合測試")
    print("=" * 60)

    try:
        from src.functions.utils.post_processing import post_process

        llm_result = {
            "body_html": """
            <p>以下是優化結果：本公司是一家專業的科技公司。</p>
            <p>我們提供軟體開發,系統整合服務.</p>
            <p>此外,我們還擁有經驗豐富的團隊.</p>
            """,
            "summary": "以下是優化結果：專業科技公司，提供軟體開發服務。",
            "tags": ["科技", "軟體開發"],
        }

        print("原始 LLM 結果:")
        print(f"body_html: {llm_result['body_html'][:100]}...")
        print(f"summary: {llm_result['summary']}")

        # 應用後處理（包含內容多樣化）
        result = post_process(llm_result, template_type="standard")

        print("\n處理後結果:")
        print(f"body_html: {result['body_html'][:100]}...")
        print(f"summary: {result['summary']}")

        # 檢查模板是否被移除
        template_removed = "以下是優化結果" not in result["body_html"]
        print(f"\n模板移除檢查: {'✅ 成功' if template_removed else '❌ 失敗'}")

    except ImportError as e:
        print(f"導入錯誤: {e}")


def main():
    """主函數"""
    print("🚀 內容多樣化效果驗證")
    print("=" * 60)

    # 運行所有測試
    test_template_removal()
    test_diversity_multiple_runs()
    test_real_world_scenarios()
    test_integration_with_post_processing()

    print("\n" + "=" * 60)
    print("✅ 驗證完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
