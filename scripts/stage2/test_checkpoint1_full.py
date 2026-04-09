#!/usr/bin/env python3
"""
完整整合測試：使用 Checkpoint 1 數據
===================================

使用真實的公司名稱測試完整的 LangGraph + Few-shot 流程
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


def test_full_integration():
    """使用 Checkpoint 1 數據測試完整流程"""

    print("=" * 80)
    print("🔧 完整整合測試：LangGraph + Few-shot + 真實公司")
    print("=" * 80)

    api_key = get_api_key()
    if not api_key:
        print("❌ 找不到 API Key")
        return False

    # 使用 Checkpoint 1 的真實公司
    test_cases = [
        {
            "name": "Case 1: 澳霸有限公司",
            "organ": "澳霸有限公司",
            "capital": 11000000,  # 1100萬
            "employees": 60,
            "founded_year": 2001,
            "user_brief": "本公司秉持永續經營的理念，擁有優秀的經營團隊，追求企業永續發展。我們重視每一位員工，提供良好的工作環境和學習成長空間。",
        },
        {
            "name": "Case 2: 正意食品",
            "organ": "正意食品股份有限公司",
            "capital": 14000000,  # 1400萬
            "employees": 90,
            "founded_year": 2004,
            "user_brief": "本公司主要經營冷凍調理食品，例如豬肉、魚、雞肉、丸類等食品零售批發。我們擁有自家工廠食品製造，多年來服務遍及中部五縣市。",
        },
    ]

    from src.functions.utils.generate_brief import generate_brief

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"📋 {case['name']}")
        print("=" * 80)

        print(f"\n🔹 測試參數:")
        print(f"   資本額: {case['capital'] / 10000:.0f}萬元")
        print(f"   員工人數: {case['employees']}人")
        print(f"   成立年份: {case['founded_year']}年")

        try:
            print(f"\n🚀 執行 generate_brief()...")
            start_time = time.time()

            result = generate_brief(
                {
                    "organ": case["organ"],
                    "capital": case["capital"],
                    "employees": case["employees"],
                    "founded_year": case["founded_year"],
                    "word_limit": 200,
                }
            )

            latency = time.time() - start_time

            print(f"✅ 成功 (耗時: {latency:.2f}秒)")
            print(f"\n📝 生成結果:")
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   Body: {result.get('body_html', 'N/A')[:200]}...")

            # 檢查數字資訊
            body = result.get("body_html", "")

            # 檢查資本額
            capital_wan = case["capital"] / 10000
            capital_str = f"{capital_wan:.0f}萬"
            capital_ok = capital_str in body or str(int(capital_wan)) in body

            # 檢查員工人數
            employees_str = f"{case['employees']}"
            employees_ok = employees_str in body

            # 檢查成立年份
            year_str = f"{case['founded_year']}"
            year_ok = year_str in body

            print(f"\n🔍 數字資訊檢查:")
            print(
                f"   {'✅' if capital_ok else '❌'} 資本額: {case['capital'] / 10000:.0f}萬"
            )
            print(
                f"   {'✅' if employees_ok else '❌'} 員工人數: {case['employees']}人"
            )
            print(f"   {'✅' if year_ok else '❌'} 成立年份: {case['founded_year']}年")

            results.append(
                {
                    "name": case["name"],
                    "success": True,
                    "capital_ok": capital_ok,
                    "employees_ok": employees_ok,
                    "year_ok": year_ok,
                    "latency": latency,
                }
            )

        except Exception as e:
            print(f"❌ 失敗: {e}")
            import traceback

            traceback.print_exc()
            results.append(
                {
                    "name": case["name"],
                    "success": False,
                    "error": str(e),
                }
            )

        if i < len(test_cases):
            print(f"\n⏱️  等待 3 秒...")
            time.sleep(3)

    # 總結
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)

    all_passed = True
    for r in results:
        if r["success"]:
            status = (
                "✅" if all([r["capital_ok"], r["employees_ok"], r["year_ok"]]) else "⚠️"
            )
            if not all([r["capital_ok"], r["employees_ok"], r["year_ok"]]):
                all_passed = False
            print(f"   {status} {r['name']}: {r['latency']:.2f}秒")
        else:
            print(f"   ❌ {r['name']}: {r['error']}")
            all_passed = False

    if all_passed:
        print(f"\n🎉 所有測試通過！")
    else:
        print(f"\n⚠️ 部分測試未通過")

    # 保存結果
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_cases": results,
        "all_passed": all_passed,
    }

    report_path = PROJECT_ROOT / "scripts" / "stage2" / "integration_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📁 報告已保存至: {report_path}")
    return all_passed


if __name__ == "__main__":
    success = test_full_integration()
    sys.exit(0 if success else 1)
