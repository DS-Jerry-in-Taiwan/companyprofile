#!/usr/bin/env python3
"""
極端多樣化測試：嘗試達到 >0.3 差異度目標
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.functions.utils.content_diversifier import (
    diversify_content,
    calculate_diversity_score,
)
import random


def test_extreme_diversity():
    """測試極端多樣化策略"""
    print("🔥 極端多樣化策略測試")
    print("=" * 60)

    # 測試內容 - 更長的文本
    test_content = """
    <p>創新科技有限公司成立於2022年，專注於人工智能和區塊鏈技術研發。</p>
    <p>公司團隊成員來自頂尖科技公司，擁有豐富的行業經驗和技術專長。</p>
    <p>我們提供AI模型訓練、區塊鏈應用開發、智能合約審計等服務。</p>
    <p>客戶包括金融科技公司、電商平台和傳統企業轉型項目。</p>
    <p>公司致力於通過技術創新幫助客戶實現數字化轉型和業務增長。</p>
    """

    print("原始內容:")
    print(test_content)
    print()

    # 生成10個多樣化版本
    results = []
    for i in range(10):
        diversified = diversify_content(test_content)
        results.append(diversified)

    # 計算差異度
    print("📊 差異度分析 (前5個版本):")
    diversity_scores = []
    comparison_count = 0

    for i in range(min(5, len(results))):
        for j in range(i + 1, min(5, len(results))):
            score = calculate_diversity_score(results[i], results[j])
            diversity_scores.append(score)
            comparison_count += 1
            print(f"  版本{i + 1} vs 版本{j + 1}: {score:.3f}")

            # 顯示具體差異
            if score > 0.3:
                print(f"    ✅ 達到目標！")
                # 顯示部分內容對比
                text1 = (
                    results[i].replace("<p>", " ").replace("</p>", " ").strip()[:100]
                )
                text2 = (
                    results[j].replace("<p>", " ").replace("</p>", " ").strip()[:100]
                )
                print(f"    版本{i + 1}: {text1}...")
                print(f"    版本{j + 1}: {text2}...")
                print()

    if diversity_scores:
        avg_diversity = sum(diversity_scores) / len(diversity_scores)
        max_diversity = max(diversity_scores)
        min_diversity = min(diversity_scores)

        print()
        print(f"📈 統計結果:")
        print(f"  比較次數: {comparison_count}")
        print(f"  平均差異度: {avg_diversity:.3f}")
        print(f"  最高差異度: {max_diversity:.3f}")
        print(f"  最低差異度: {min_diversity:.3f}")
        print(f"  目標差異度: > 0.3")
        print(f"  是否達標: {'✅' if avg_diversity > 0.3 else '❌'}")

        # 顯示達到目標的版本
        above_threshold = [s for s in diversity_scores if s > 0.3]
        if above_threshold:
            print(
                f"  ✅ 有 {len(above_threshold)}/{len(diversity_scores)} 次比較達到目標"
            )
        else:
            print(f"  ❌ 沒有比較達到目標")
    else:
        print("❌ 無法計算差異度")

    return avg_diversity > 0.3 if diversity_scores else False


if __name__ == "__main__":
    success = test_extreme_diversity()
    sys.exit(0 if success else 1)
