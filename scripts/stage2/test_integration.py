#!/usr/bin/env python3
"""
整合測試：驗證 LangGraph 流程 + Few-shot 方案
==============================================

測試整合後的 generate_brief() 是否正確使用 LangGraph 流程
並確認 Few-shot Prompt 被正確傳遞

使用方法:
  python3 test_integration.py

"""

import json
import os
import sys
import time
from pathlib import Path

# 確保 src 目錄在 Python 路徑中
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_api_key():
    """獲取 API Key"""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                    api_key = line.split("=", 1)[1].strip()
                    if api_key:
                        return api_key
    return None


def test_langgraph_import():
    """測試 LangGraph 模組是否可以正確導入"""

    print("=" * 80)
    print("測試 1: LangGraph 模組導入")
    print("=" * 80)

    try:
        from src.langgraph.company_brief_graph import (
            generate_company_brief,
            create_company_brief_graph,
        )

        print("✅ LangGraph 模組導入成功")
        return True
    except ImportError as e:
        print(f"❌ LangGraph 模組導入失敗: {e}")
        return False


def test_generate_brief_import():
    """測試 generate_brief 是否可以正確導入"""

    print("\n" + "=" * 80)
    print("測試 2: generate_brief 模組導入")
    print("=" * 80)

    try:
        from src.functions.utils.generate_brief import generate_brief

        print("✅ generate_brief 模組導入成功")
        return True
    except ImportError as e:
        print(f"❌ generate_brief 模組導入失敗: {e}")
        return False


def test_prompt_builder():
    """測試 prompt_builder 的 Few-shot 功能"""

    print("\n" + "=" * 80)
    print("測試 3: prompt_builder Few-shot 功能")
    print("=" * 80)

    from src.functions.utils.prompt_builder import (
        build_generate_prompt,
        validate_info_usage,
    )

    # 構建 Prompt
    prompt = build_generate_prompt(
        organ="測試公司",
        capital=10000000,
        employees=50,
        founded_year=2018,
        word_limit=200,
    )

    # 檢查是否包含 Few-shot 內容
    checks = {
        "包含 Few-shot 範例": "範例參考" in prompt,
        "包含數字標記": "[資本額]" in prompt,
        "包含檢查清單": "生成後檢查清單" in prompt,
    }

    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}: {'通過' if result else '失敗'}")
        if not result:
            all_passed = False

    # 測試 Validation
    test_output = "測試公司成立於2018年，資本額1000萬元，員工人數約50人。"
    is_valid, missing = validate_info_usage(
        test_output,
        capital=10000000,
        employees=50,
        founded_year=2018,
    )

    print(f"\n  Validation 測試:")
    print(f"  {'✅' if is_valid else '❌'} 通過: {is_valid}")
    if missing:
        print(f"     缺失: {', '.join(missing)}")

    if not is_valid:
        all_passed = False

    return all_passed


def test_full_integration():
    """完整整合測試（需要 LangGraph 可用）"""

    print("\n" + "=" * 80)
    print("測試 4: 完整整合測試（LangGraph + Few-shot）")
    print("=" * 80)

    api_key = get_api_key()
    if not api_key:
        print("⚠️  找不到 API Key，跳過完整整合測試")
        return None

    try:
        from src.functions.utils.generate_brief import generate_brief

        test_data = {
            "organ": "測試科技有限公司",
            "capital": 10000000,
            "employees": 50,
            "founded_year": 2018,
            "word_limit": 200,
        }

        print(f"\n  公司: {test_data['organ']}")
        print(f"  資本額: {test_data['capital'] / 10000:.0f}萬元")
        print(f"  員工人數: {test_data['employees']}人")
        print(f"  成立年份: {test_data['founded_year']}年")

        print(f"\n  正在執行 generate_brief()...")
        start_time = time.time()

        result = generate_brief(test_data)

        latency = time.time() - start_time

        print(f"\n✅ 生成成功 (耗時: {latency:.2f}秒)")
        print(f"\n  結果預覽:")
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  Body: {result.get('body_html', 'N/A')[:100]}...")
        print(f"  Processing Mode: {result.get('processing_mode', 'N/A')}")

        # 檢查 processing_mode 是否為 langgraph
        if result.get("processing_mode") != "langgraph":
            print(f"\n❌ processing_mode 不正確: {result.get('processing_mode')}")
            return False

        # 檢查是否包含數字資訊
        body = result.get("body_html", "")
        capital_ok = "1000" in body or "1000萬" in body or "10,000,000" in body
        employees_ok = "50" in body
        year_ok = "2018" in body

        print(f"\n  數字資訊檢查:")
        print(f"  {'✅' if capital_ok else '❌'} 包含資本額")
        print(f"  {'✅' if employees_ok else '❌'} 包含員工人數")
        print(f"  {'✅' if year_ok else '❌'} 包含成立年份")

        return all([capital_ok, employees_ok, year_ok])

    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主測試函數"""

    print("\n🔧 Few-shot + LangGraph 整合測試\n")

    results = []

    # 測試 1: LangGraph 模組導入
    result1 = test_langgraph_import()
    results.append(("LangGraph 模組導入", result1))

    if not result1:
        print("\n❌ LangGraph 不可用，無法繼續測試")
        return 1

    # 測試 2: generate_brief 模組導入
    result2 = test_generate_brief_import()
    results.append(("generate_brief 模組導入", result2))

    # 測試 3: prompt_builder Few-shot 功能
    result3 = test_prompt_builder()
    results.append(("prompt_builder Few-shot", result3))

    # 測試 4: 完整整合測試
    result4 = test_full_integration()
    if result4 is not None:
        results.append(("完整整合測試", result4))

    # 總結
    print("\n" + "=" * 80)
    print("📊 測試結果總覽")
    print("=" * 80)

    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 所有測試通過！")
        return 0
    else:
        print("\n⚠️ 部分測試未通過")
        return 1


if __name__ == "__main__":
    sys.exit(main())
