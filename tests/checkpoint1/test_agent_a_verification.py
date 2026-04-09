"""
測試腳本：驗證 Agent A 修復 - 選填欄位傳遞
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.functions.utils.prompt_builder import build_generate_prompt


def test_optional_fields_in_prompt():
    """測試選填欄位是否被正確包含在 prompt 中"""

    # Test 1: 全部選填欄位都提供
    prompt = build_generate_prompt(
        organ="測試公司",
        organ_no="12345678",
        capital=5000,
        employees=100,
        founded_year=2015,
        word_limit=100,
    )

    print("=== Test 1: 所有選填欄位都提供 ===")
    print(prompt)
    print("\n" + "=" * 50 + "\n")

    assert "資本額：5,000 千元" in prompt, "資本額未正確格式化"
    assert "員工人數：約 100 人" in prompt, "員工人數未正確格式化"
    assert "成立年份：西元 2015 年" in prompt, "成立年份未正確格式化"

    # Test 2: 部分選填欄位提供
    prompt = build_generate_prompt(
        organ="測試公司",
        organ_no="12345678",
        capital=10000,
        # employees 和 founded_year 不提供
        word_limit=100,
    )

    print("=== Test 2: 僅提供資本額 ===")
    print(prompt)
    print("\n" + "=" * 50 + "\n")

    assert "資本額：10,000 千元" in prompt, "資本額未正確格式化"
    assert "員工人數" not in prompt, "不應包含員工人數"
    assert "成立年份" not in prompt, "不應包含成立年份"

    # Test 3: 無選填欄位
    prompt = build_generate_prompt(
        organ="測試公司", organ_no="12345678", word_limit=100
    )

    print("=== Test 3: 無選填欄位 ===")
    print(prompt)
    print("\n" + "=" * 50 + "\n")

    assert "資本額" not in prompt, "不應包含資本額"
    assert "員工人數" not in prompt, "不應包含員工人數"
    assert "成立年份" not in prompt, "不應包含成立年份"

    print("✅ 所有測試通過！選填欄位已正確傳遞到 prompt")


if __name__ == "__main__":
    test_optional_fields_in_prompt()
