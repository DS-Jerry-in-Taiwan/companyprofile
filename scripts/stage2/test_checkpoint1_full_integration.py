#!/usr/bin/env python3
"""
完整整合測試：使用 Checkpoint 1 全部測試數據
=============================================

使用 Checkpoint 1 的 10 個真實公司測試完整的 LangGraph + Few-shot 流程
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


def load_checkpoint1_data():
    """載入 Checkpoint 1 測試數據"""
    data_path = (
        PROJECT_ROOT
        / "docs"
        / "test_report"
        / "v0.0.1"
        / "phase14"
        / "checkpoint1"
        / "test_data"
        / "structured_test_data.json"
    )

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["test_cases"]


def test_checkpoint1_cases():
    """使用 Checkpoint 1 數據測試完整流程"""

    print("=" * 80)
    print("🔧 完整整合測試：LangGraph + Few-shot + Checkpoint 1 數據")
    print("=" * 80)

    api_key = get_api_key()
    if not api_key:
        print("❌ 找不到 API Key")
        return False

    # 載入 Checkpoint 1 數據
    test_cases = load_checkpoint1_data()
    print(f"\n📊 載入 {len(test_cases)} 個測試案例")

    from src.functions.utils.generate_brief import generate_brief

    results = []
    all_passed = True

    for i, case in enumerate(test_cases, 1):  # 測試所有案例
        print(f"\n{'=' * 80}")
        print(f"📋 Case {case['case_id']}: {case['company']['name']}")
        print("=" * 80)

        company_name = case["company"]["name"]
        registration_id = case["company"]["registration_id"]
        industry = case["industry"]["type"]
        before_text = case["before_text"]

        # 模擬選填欄位
        test_capital = 10000000 + (i * 1000000)  # 1000萬, 1100萬, etc.
        test_employees = 50 + (i * 10)  # 50人, 60人, etc.
        test_founded_year = 2000 + i  # 2001, 2002, etc.

        print(f"\n🔹 測試參數:")
        print(f"   公司: {company_name}")
        print(f"   統編: {registration_id}")
        print(f"   產業: {industry}")
        print(f"   資本額: {test_capital / 10000:.0f}萬元")
        print(f"   員工人數: {test_employees}人")
        print(f"   成立年份: {test_founded_year}年")
        print(f"   原始素材: {before_text[:50]}...")

        try:
            print(f"\n🚀 執行 generate_brief()...")
            start_time = time.time()

            result = generate_brief(
                {
                    "organ": company_name,
                    "organNo": registration_id,
                    "brief": before_text,
                    "capital": test_capital,
                    "employees": test_employees,
                    "founded_year": test_founded_year,
                    "word_limit": 200,
                }
            )

            latency = time.time() - start_time

            print(f"✅ 成功 (耗時: {latency:.2f}秒)")

            # 檢查數字資訊
            body = result.get("body_html", "")

            # 檢查資本額
            capital_wan = test_capital / 10000
            capital_str = f"{capital_wan:.0f}萬"
            capital_ok = capital_str in body or str(int(capital_wan)) in body

            # 檢查員工人數
            employees_str = f"{test_employees}"
            employees_ok = employees_str in body

            # 檢查成立年份
            year_str = f"{test_founded_year}"
            year_ok = year_str in body

            # 檢查是否包含公司名稱
            company_ok = company_name in body

            print(f"\n🔍 數字資訊檢查:")
            print(
                f"   {'✅' if capital_ok else '❌'} 資本額: {test_capital / 10000:.0f}萬"
            )
            print(f"   {'✅' if employees_ok else '❌'} 員工人數: {test_employees}人")
            print(f"   {'✅' if year_ok else '❌'} 成立年份: {test_founded_year}年")
            print(f"   {'✅' if company_ok else '❌'} 公司名稱: {company_name}")

            # 計算使用率
            total_checks = 4
            passed_checks = sum([capital_ok, employees_ok, year_ok, company_ok])
            usage_rate = (passed_checks / total_checks) * 100

            print(
                f"\n📊 資訊使用率: {usage_rate:.0f}% ({passed_checks}/{total_checks})"
            )

            result_data = {
                "case_id": case["case_id"],
                "company_name": company_name,
                "success": True,
                "capital_ok": capital_ok,
                "employees_ok": employees_ok,
                "year_ok": year_ok,
                "company_ok": company_ok,
                "usage_rate": usage_rate,
                "latency": latency,
                "output": result.get("body_html", ""),  # 保存 LLM 回應
                "title": result.get("title", ""),
                "summary": result.get("summary", ""),
            }

            results.append(result_data)

            if not all([capital_ok, employees_ok, year_ok, company_ok]):
                all_passed = False

        except Exception as e:
            print(f"❌ 失敗: {e}")
            import traceback

            traceback.print_exc()
            results.append(
                {
                    "case_id": case["case_id"],
                    "company_name": company_name,
                    "success": False,
                    "error": str(e),
                }
            )
            all_passed = False

        if i < len(test_cases):
            print(f"\n⏱️  等待 3 秒...")
            time.sleep(3)

    # 總結
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)

    successful_cases = [r for r in results if r.get("success", False)]
    failed_cases = [r for r in results if not r.get("success", False)]

    print(f"\n📈 統計:")
    print(f"   總案例數: {len(results)}")
    print(f"   成功: {len(successful_cases)}")
    print(f"   失敗: {len(failed_cases)}")

    if successful_cases:
        avg_latency = sum(r["latency"] for r in successful_cases) / len(
            successful_cases
        )
        avg_usage_rate = sum(r["usage_rate"] for r in successful_cases) / len(
            successful_cases
        )

        print(f"   平均耗時: {avg_latency:.2f}秒")
        print(f"   平均使用率: {avg_usage_rate:.0f}%")

    print(f"\n📋 各案例詳情:")
    for r in results:
        if r.get("success", False):
            status = "✅" if r["usage_rate"] == 100 else "⚠️"
            print(
                f"   {status} Case {r['case_id']} ({r['company_name']}): {r['usage_rate']:.0f}% 使用率, {r['latency']:.2f}秒"
            )
        else:
            print(
                f"   ❌ Case {r['case_id']} ({r['company_name']}): {r.get('error', 'Unknown error')}"
            )

    if all_passed:
        print(f"\n🎉 所有測試通過！")
    else:
        print(f"\n⚠️ 部分測試未通過")

    # 保存結果
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_cases": len(results),
        "successful_cases": len(successful_cases),
        "failed_cases": len(failed_cases),
        "all_passed": all_passed,
        "results": results,
    }

    report_path = (
        PROJECT_ROOT / "scripts" / "stage2" / "checkpoint1_integration_report.json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📁 報告已保存至: {report_path}")
    return all_passed


if __name__ == "__main__":
    success = test_checkpoint1_cases()
    sys.exit(0 if success else 1)
