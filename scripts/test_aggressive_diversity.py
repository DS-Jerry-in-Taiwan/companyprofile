#!/usr/bin/env python3
"""
測試激進的多樣化策略
目標：達到差異度 > 0.3 的目標
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.functions.utils.content_diversifier import (
    diversify_content,
    calculate_diversity_score,
)
import random


def test_aggressive_diversity():
    """測試激進的多樣化策略"""
    print("🎯 激進多樣化策略測試")
    print("=" * 60)

    # 測試內容
    test_content = """
    <p>以下是優化結果：本公司是一家非常專業的科技公司。</p>
    <p>我們提供世界一流的軟體開發和系統整合服務。</p>
    <p>此外，公司擁有經驗豐富的技術團隊，採用最先進的技術。</p>
    <p>具體來說，我們的服務包括企業系統開發、移動應用開發。</p>
    <p>不僅提供開發服務，而且提供技術諮詢和培訓。</p>
    """

    print("原始內容:")
    print(test_content)
    print()

    # 生成10個多樣化版本
    results = []
    for i in range(10):
        diversified = diversify_content(test_content)
        results.append(diversified)
        print(f"版本 {i + 1}:")
        print(diversified[:200] + "..." if len(diversified) > 200 else diversified)
        print()

    # 計算差異度
    print("📊 差異度分析:")
    diversity_scores = []
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            score = calculate_diversity_score(results[i], results[j])
            diversity_scores.append(score)
            print(f"  版本{i + 1} vs 版本{j + 1}: {score:.3f}")

    avg_diversity = (
        sum(diversity_scores) / len(diversity_scores) if diversity_scores else 0
    )
    max_diversity = max(diversity_scores) if diversity_scores else 0
    min_diversity = min(diversity_scores) if diversity_scores else 0

    print()
    print(f"📈 統計結果:")
    print(f"  平均差異度: {avg_diversity:.3f}")
    print(f"  最高差異度: {max_diversity:.3f}")
    print(f"  最低差異度: {min_diversity:.3f}")
    print(f"  目標差異度: > 0.3")
    print(f"  是否達標: {'✅' if avg_diversity > 0.3 else '❌'}")

    # 測試模板移除效果
    print()
    print("🔍 模板移除測試:")
    test_cases = [
        ("此外，我們還提供服務。", "我們還提供服務。"),
        ("具體來說，包括三項服務。", "包括三項服務。"),
        ("不僅提供A，而且提供B。", "提供A，提供B。"),
        ("不僅產品好，而且價格便宜。", "產品好，價格便宜。"),
    ]

    for original, expected in test_cases:
        result = diversify_content(f"<p>{original}</p>")
        # 移除HTML標籤
        result_text = result.replace("<p>", "").replace("</p>", "").strip()
        status = "✅" if result_text == expected else "❌"
        print(f"  {status} 輸入: {original}")
        print(f"     輸出: {result_text}")
        print(f"     預期: {expected}")

    return avg_diversity > 0.3


if __name__ == "__main__":
    success = test_aggressive_diversity()
    sys.exit(0 if success else 1)
