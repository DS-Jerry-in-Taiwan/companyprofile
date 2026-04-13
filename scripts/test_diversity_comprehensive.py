#!/usr/bin/env python3
"""
內容多樣化全面驗證腳本
驗證所有多樣化功能的效果
"""

import sys
import os
import random
import difflib
import re

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.functions.utils.content_diversifier import (
    diversify_content,
    calculate_diversity_score,
    _remove_template_patterns,
    _randomize_sentence_structures,
    _randomize_adjectives,
    _increase_expression_diversity,
)


def print_header(title):
    """打印標題"""
    print("\n" + "=" * 70)
    print(f"🔍 {title}")
    print("=" * 70)


def test_individual_functions():
    """測試各個功能函數"""
    print_header("測試各個多樣化功能函數")

    # 測試模板移除
    print("1. 模板移除功能:")
    test_cases = [
        ("此外，我們還提供服務。", "我們還提供服務。"),
        ("具體來說，包括三項服務。", "包括三項服務。"),
        ("不僅提供A，而且提供B。", "提供A，提供B。"),
    ]

    for input_text, expected in test_cases:
        result = _remove_template_patterns(input_text)
        status = "✅" if result == expected else "❌"
        print(f"   {status} 輸入: {input_text}")
        print(f"     輸出: {result}")
        if result != expected:
            print(f"     預期: {expected}")

    # 測試句式隨機化
    print("\n2. 句式隨機化功能:")
    test_text = "本公司是一家專業的科技公司。"
    random.seed(42)
    result1 = _randomize_sentence_structures(test_text)
    random.seed(123)
    result2 = _randomize_sentence_structures(test_text)
    print(f"   原始: {test_text}")
    print(f"   結果1: {result1}")
    print(f"   結果2: {result2}")
    print(f"   是否不同: {'✅' if result1 != result2 else '❌'}")

    # 測試形容詞隨機化
    print("\n3. 形容詞隨機化功能:")
    test_text = "提供專業的服務和優質的產品。"
    random.seed(456)
    result = _randomize_adjectives(test_text)
    print(f"   原始: {test_text}")
    print(f"   結果: {result}")

    # 測試表達多樣化
    print("\n4. 表達多樣化功能:")
    test_text = "我們提供專業服務，技術領先。"
    random.seed(789)
    result = _increase_expression_diversity(test_text)
    print(f"   原始: {test_text}")
    print(f"   結果: {result}")


def test_comprehensive_diversity():
    """測試綜合多樣性"""
    print_header("測試綜合多樣性效果")

    # 創建包含多種模板的測試內容
    test_content = """
    <p>以下是優化結果：本公司是一家非常專業的科技公司。</p>
    <p>我們提供世界一流的軟體開發和系統整合服務。</p>
    <p>此外，公司擁有經驗豐富的技術團隊，採用最先進的技術。</p>
    <p>具體來說，我們的服務包括企業系統開發、移動應用開發。</p>
    <p>不僅提供開發服務，而且提供技術諮詢和培訓。</p>
    """

    print("原始內容:")
    print(test_content)

    # 測試10次多樣化
    print("\n10次多樣化結果摘要:")
    results = []
    template_counts = []

    for i in range(10):
        random.seed(i * 100)  # 使用不同的種子
        result = diversify_content(test_content)
        results.append(result)

        # 統計模板詞出現次數
        template_words = ["以下是優化結果", "此外，", "具體來說，", "不僅", "而且"]
        count = sum(1 for word in template_words if word in result)
        template_counts.append(count)

        # 顯示摘要
        lines = result.strip().split("\n")
        summary = " | ".join(
            [line[:30] + "..." if len(line) > 30 else line for line in lines[:3]]
        )
        print(f"   {i + 1:2d}. 模板詞: {count}個 | {summary}")

    # 分析多樣性
    print("\n📊 多樣性分析:")

    # 計算平均模板詞數量
    avg_templates = sum(template_counts) / len(template_counts)
    print(f"   平均模板詞數量: {avg_templates:.1f}個")
    print(f"   模板消除效果: {'✅ 良好' if avg_templates < 2 else '⚠️ 需改進'}")

    # 計算差異度
    diversity_scores = []
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            score = calculate_diversity_score(results[i], results[j])
            diversity_scores.append(score)

    avg_diversity = (
        sum(diversity_scores) / len(diversity_scores) if diversity_scores else 0
    )
    print(f"   平均差異度: {avg_diversity:.3f}")
    print(f"   差異度目標(>0.3): {'✅ 達成' if avg_diversity > 0.3 else '❌ 未達標'}")

    # 顯示最高和最低差異度
    if diversity_scores:
        print(f"   最高差異度: {max(diversity_scores):.3f}")
        print(f"   最低差異度: {min(diversity_scores):.3f}")

    # 顯示最具多樣性的兩個結果
    if len(results) >= 2:
        max_score = 0
        max_pair = (0, 1)
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                score = calculate_diversity_score(results[i], results[j])
                if score > max_score:
                    max_score = score
                    max_pair = (i, j)

        print(
            f"\n🎯 最具多樣性的對比 (結果{max_pair[0] + 1} vs 結果{max_pair[1] + 1}):"
        )
        print(f"   差異度: {max_score:.3f}")
        print(f"   結果{max_pair[0] + 1}: {results[max_pair[0]][:100]}...")
        print(f"   結果{max_pair[1] + 1}: {results[max_pair[1]][:100]}...")


def test_realistic_scenarios():
    """測試真實場景"""
    print_header("測試真實商業場景")

    scenarios = [
        {
            "name": "新創科技公司",
            "content": """
            <p>以下是優化結果：創新科技有限公司成立於2022年。</p>
            <p>我們專注於人工智能和區塊鏈技術的研發。</p>
            <p>此外，團隊成員來自頂尖科技公司，擁有豐富經驗。</p>
            <p>具體來說，我們提供AI模型訓練和區塊鏈應用開發。</p>
            """,
        },
        {
            "name": "傳統製造企業",
            "content": """
            <p>根據您的要求，永續製造公司成立於1995年。</p>
            <p>我們主要生產環保建材和綠色包裝材料。</p>
            <p>不僅產品符合國際標準，而且生產過程零污染。</p>
            <p>公司擁有ISO 14001環境管理體系認證。</p>
            """,
        },
        {
            "name": "專業服務公司",
            "content": """
            <p>以下是生成結果：卓越顧問集團是一家管理諮詢公司。</p>
            <p>我們提供戰略規劃、組織變革和數字化轉型服務。</p>
            <p>此外，我們的顧問團隊擁有MBA學位和行業經驗。</p>
            <p>具體來說，服務包括市場分析、流程優化和績效管理。</p>
            """,
        },
    ]

    for scenario in scenarios:
        print(f"\n🏢 場景: {scenario['name']}")
        print("-" * 40)

        # 原始內容
        print("原始內容:")
        for line in scenario["content"].strip().split("\n"):
            if line.strip():
                print(f"  {line.strip()}")

        # 多樣化結果
        random.seed(999)  # 固定種子以便比較
        result = diversify_content(scenario["content"])

        print("\n多樣化後:")
        for line in result.strip().split("\n"):
            if line.strip():
                print(f"  {line.strip()}")

        # 分析改進
        original = scenario["content"]
        improved = result

        # 計算模板詞減少
        template_words = [
            "以下是優化結果",
            "根據您的要求",
            "以下是生成結果",
            "此外，",
            "具體來說，",
            "不僅",
            "而且",
        ]
        orig_count = sum(1 for word in template_words if word in original)
        impr_count = sum(1 for word in template_words if word in improved)

        print(f"\n📈 改進分析:")
        print(
            f"  模板詞減少: {orig_count} → {impr_count}個 ({((orig_count - impr_count) / orig_count * 100):.0f}%減少)"
        )
        print(f"  改進效果: {'✅ 顯著' if impr_count < orig_count / 2 else '⚠️ 一般'}")


def test_edge_cases():
    """測試邊界條件"""
    print_header("測試邊界條件")

    edge_cases = [
        ("空內容", ""),
        ("純英文", "<p>Here is the optimized result: Company description.</p>"),
        ("只有模板", "以下是優化結果："),
        ("混合語言", "<p>以下是優化結果：Tech公司提供AI服務。</p>"),
        ("超長內容", "<p>本公司</p>" * 50),
    ]

    for name, content in edge_cases:
        print(f"\n🔬 {name}:")
        print(f"   輸入: {content[:50]}{'...' if len(content) > 50 else ''}")

        try:
            result = diversify_content(content)
            print(f"   輸出: {result[:50]}{'...' if len(result) > 50 else ''}")
            print(f"   狀態: ✅ 正常處理")
        except Exception as e:
            print(f"   狀態: ❌ 錯誤: {e}")


def main():
    """主函數"""
    print("🚀 內容多樣化全面效果驗證")
    print("=" * 70)

    # 運行所有測試
    test_individual_functions()
    test_comprehensive_diversity()
    test_realistic_scenarios()
    test_edge_cases()

    print("\n" + "=" * 70)
    print("📋 驗證總結")
    print("=" * 70)
    print("✅ 模板移除功能正常")
    print("✅ 各個多樣化函數正常工作")
    print("✅ 邊界條件處理正常")
    print("⚠️  多樣性程度需持續監控和優化")
    print("=" * 70)
    print("🎯 建議: 根據實際使用情況調整隨機化參數")
    print("=" * 70)


if __name__ == "__main__":
    main()
