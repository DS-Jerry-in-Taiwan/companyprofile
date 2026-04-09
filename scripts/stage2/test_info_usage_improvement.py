#!/usr/bin/env python3
"""
Stage 2 - 資訊使用率優化測試
==============================

測試改進後的 Prompt 是否能提升資訊使用率

使用方法:
  python3 test_info_usage_improvement.py

"""

import json
import sys
from pathlib import Path

# 引入修改後的 prompt_builder
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "src" / "functions" / "utils")
)
from prompt_builder import build_generate_prompt


def test_prompt_building():
    """測試 Prompt 構建"""

    print("=" * 80)
    print("資訊使用率優化 - Prompt 改進測試")
    print("=" * 80)

    # 測試案例 1: 完整資訊
    print("\n📋 測試案例 1: 完整資訊")
    print("-" * 80)

    prompt1 = build_generate_prompt(
        organ="測試科技有限公司",
        organ_no="12345678",
        capital=5000000,
        employees=100,
        founded_year=2015,
        user_brief="專注於 AI 軟體開發",
        word_limit=200,
    )

    print(prompt1)

    # 檢查是否包含硬性要求
    has_required_section = "硬性要求" in prompt1
    has_capital = "500" in prompt1 or "500萬" in prompt1 or "5,000,000" in prompt1
    has_employees = "100" in prompt1
    has_founded_year = "2015" in prompt1

    print(f"\n✅ 檢查結果:")
    print(f"  - 包含硬性要求章節: {'✅' if has_required_section else '❌'}")
    print(f"  - 包含資本額資訊: {'✅' if has_capital else '❌'}")
    print(f"  - 包含員工人數: {'✅' if has_employees else '❌'}")
    print(f"  - 包含成立年份: {'✅' if has_founded_year else '❌'}")

    # 測試案例 2: 部分資訊
    print("\n\n📋 測試案例 2: 只有資本額")
    print("-" * 80)

    prompt2 = build_generate_prompt(
        organ="簡化測試公司", capital=10000000, word_limit=150
    )

    print(prompt2)

    has_only_capital = "1000" in prompt2 or "1000萬" in prompt2
    print(f"\n✅ 檢查結果:")
    print(f"  - 正確顯示資本額: {'✅' if has_only_capital else '❌'}")
    print(f"  - 無員工人數要求: {'✅' if '員工人數' not in prompt2 else '❌'}")
    print(f"  - 無成立年份要求: {'✅' if '成立年份' not in prompt2 else '❌'}")

    # 測試案例 3: 無選填資訊
    print("\n\n📋 測試案例 3: 無選填資訊")
    print("-" * 80)

    prompt3 = build_generate_prompt(
        organ="基礎測試公司", user_brief="一般企業", word_limit=200
    )

    print(prompt3)

    no_required_section = "硬性要求" not in prompt3
    print(f"\n✅ 檢查結果:")
    print(f"  - 無硬性要求章節（正確）: {'✅' if no_required_section else '❌'}")

    # 總結
    print("\n" + "=" * 80)
    print("🎯 改進效果評估")
    print("=" * 80)

    all_passed = (
        has_required_section
        and has_capital
        and has_employees
        and has_founded_year
        and has_only_capital
        and no_required_section
    )

    if all_passed:
        print("\n✅ 所有測試通過！Prompt 改進成功")
        print("\n改進內容:")
        print("  1. ✅ 新增『硬性要求』章節")
        print("  2. ✅ 明確列出必須使用的資訊")
        print("  3. ✅ 強調不得遺漏數值資訊")
        print("  4. ✅ 動態調整（無選填資訊時不顯示要求）")
        return 0
    else:
        print("\n⚠️ 部分測試未通過，需要檢查")
        return 1


if __name__ == "__main__":
    exit(test_prompt_building())
