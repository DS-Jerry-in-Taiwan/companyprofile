#!/usr/bin/env python3
"""
Few-shot + Validation 方案測試
==============================

測試改進後的 Prompt（含 Few-shot 範例）是否能提升資訊使用率
並驗證 Validation 機制是否正確檢測缺失資訊

使用方法:
  python3 test_fewshot_validation.py

"""

import json
import sys
from pathlib import Path

# 引入修改後的 prompt_builder
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "src" / "functions" / "utils")
)
from prompt_builder import build_generate_prompt, validate_info_usage


def test_prompt_structure():
    """測試 Prompt 結構是否正確包含 Few-shot 範例"""

    print("=" * 80)
    print("測試 1: Prompt 結構檢查")
    print("=" * 80)

    prompt = build_generate_prompt(
        organ="測試科技有限公司",
        organ_no="12345678",
        capital=5000000,  # 500萬
        employees=100,
        founded_year=2015,
        word_limit=200,
    )

    # 檢查是否包含 Few-shot 範例
    checks = {
        "包含 Few-shot 範例標題": "範例參考" in prompt,
        "包含範例一": "範例一：包含資本額與員工人數" in prompt,
        "包含範例二": "範例二：包含成立年份" in prompt,
        "包含數字標記": "[資本額]" in prompt,
        "包含檢查清單": "生成後檢查清單" in prompt,
        "硬性要求更新": "檢查點" in prompt,
    }

    print("\n✅ Prompt 結構檢查結果:")
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}: {'通過' if result else '失敗'}")
        if not result:
            all_passed = False

    # 顯示部分 Prompt 內容
    print("\n📋 生成的 Prompt 預覽（前 1000 字）:")
    print("-" * 80)
    print(prompt[:1000])
    print("...")

    return all_passed


def test_validation_function():
    """測試 Validation 函數"""

    print("\n" + "=" * 80)
    print("測試 2: Validation 函數測試")
    print("=" * 80)

    test_cases = [
        {
            "name": "完整使用所有數字",
            "output": "測試公司成立於2015年，資本額500萬元，員工人數約100人。",
            "capital": 5000000,
            "employees": 100,
            "founded_year": 2015,
            "expected_valid": True,
        },
        {
            "name": "缺少資本額",
            "output": "測試公司成立於2015年，員工人數約100人。",
            "capital": 5000000,
            "employees": 100,
            "founded_year": 2015,
            "expected_valid": False,
        },
        {
            "name": "缺少員工人數",
            "output": "測試公司成立於2015年，資本額500萬元。",
            "capital": 5000000,
            "employees": 100,
            "founded_year": 2015,
            "expected_valid": False,
        },
        {
            "name": "缺少成立年份",
            "output": "測試公司資本額500萬元，員工人數約100人。",
            "capital": 5000000,
            "employees": 100,
            "founded_year": 2015,
            "expected_valid": False,
        },
        {
            "name": "測試億元格式",
            "output": "大公司成立於2020年，資本額2.50億元。",
            "capital": 250000000,  # 2.5億
            "employees": None,
            "founded_year": 2020,
            "expected_valid": True,
        },
    ]

    all_passed = True
    print("\n🧪 Validation 測試結果:")

    for case in test_cases:
        is_valid, missing = validate_info_usage(
            case["output"],
            capital=case.get("capital"),
            employees=case.get("employees"),
            founded_year=case.get("founded_year"),
        )

        expected = case["expected_valid"]
        passed = is_valid == expected

        status = "✅" if passed else "❌"
        print(f"\n  {status} {case['name']}")
        print(f"     輸出: {case['output']}")
        print(
            f"     預期: {'通過' if expected else '失敗'} | 實際: {'通過' if is_valid else '失敗'}"
        )

        if missing:
            print(f"     檢測到缺失: {', '.join(missing)}")

        if not passed:
            all_passed = False

    return all_passed


def test_edge_cases():
    """測試邊界情況"""

    print("\n" + "=" * 80)
    print("測試 3: 邊界情況測試")
    print("=" * 80)

    test_cases = [
        {
            "name": "無選填資訊時不應顯示 Few-shot",
            "prompt_args": {
                "organ": "簡單公司",
                "word_limit": 200,
            },
            "check": lambda p: "Few-shot" not in p and "範例參考" not in p,
        },
        {
            "name": "只有資本額時顯示對應範例",
            "prompt_args": {
                "organ": "資本公司",
                "capital": 10000000,
                "word_limit": 200,
            },
            "check": lambda p: "[資本額]" in p and "範例一" in p,
        },
    ]

    all_passed = True
    print("\n🔍 邊界情況測試:")

    for case in test_cases:
        prompt = build_generate_prompt(**case["prompt_args"])
        result = case["check"](prompt)

        status = "✅" if result else "❌"
        print(f"  {status} {case['name']}: {'通過' if result else '失敗'}")

        if not result:
            all_passed = False

    return all_passed


def generate_summary():
    """生成測試總結"""

    print("\n" + "=" * 80)
    print("📝 Few-shot + Validation 方案測試總結")
    print("=" * 80)

    summary = """
📋 改進內容：

1. ✅ Few-shot 範例
   - 添加了 3 個完整範例
   - 展示正確與錯誤的對比
   - 明確指出錯誤原因

2. ✅ 數字標記法
   - 使用 [資本額]: xxx 格式
   - 明確標記必須使用的數字
   - 降低 LLM 自行解釋的空間

3. ✅ 自我檢查清單
   - 提示 LLM 生成後自我檢查
   - 列出必須包含的數字

4. ✅ Validation 函數
   - 後處理驗證機制
   - 精確檢測數字是否被使用
   - 支持多種數字格式

🎯 預期效果：
- Few-shot 範例可以顯著提升 LLM 的服從性
- Validation 作為保底機制，確保資訊被使用
- 整體資訊使用率預計可從 46.7% 提升至 80%+

⚠️ 注意事項：
- 需在實際 API 調用中測試效果
- Validation 失敗時需要實現 Re-prompting 邏輯
"""
    print(summary)


if __name__ == "__main__":
    results = []

    # 運行所有測試
    results.append(("Prompt 結構", test_prompt_structure()))
    results.append(("Validation 函數", test_validation_function()))
    results.append(("邊界情況", test_edge_cases()))

    # 生成總結
    generate_summary()

    # 最終結果
    print("\n" + "=" * 80)
    print("📊 測試結果總覽")
    print("=" * 80)

    all_passed = all(r[1] for r in results)
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有測試通過！方案已準備就緒")
        sys.exit(0)
    else:
        print("⚠️ 部分測試未通過，請檢查")
        sys.exit(1)
