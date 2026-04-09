#!/usr/bin/env python3
"""
使用 Checkpoint 1 測試數據驗證 Few-shot 方案
=============================================

使用 /docs/test_report/v0.0.1/phase14/checkpoint1/test_data/structured_test_data.json
中的真實案例來測試 Few-shot + Validation 方案的效果

使用方法:
  python3 test_checkpoint1_cases.py

"""

import json
import os
import sys
import time
from pathlib import Path

# 引入修改後的 prompt_builder
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "src" / "functions" / "utils")
)
from prompt_builder import build_generate_prompt, validate_info_usage


def load_checkpoint1_data():
    """載入 Checkpoint 1 測試數據"""
    data_path = (
        Path(__file__).parent.parent.parent
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


def get_api_key():
    """獲取 API Key"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                    api_key = line.split("=", 1)[1].strip()
                    if api_key:
                        return api_key
    return None


def call_llm_api(prompt, api_key, max_retries=3):
    """調用 Gemini API"""
    try:
        import requests

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800},
        }

        start_time = time.time()

        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                latency = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    if "candidates" in data and len(data["candidates"]) > 0:
                        result = data["candidates"][0]["content"]["parts"][0]["text"]
                        return True, result.strip(), latency
                    return False, "API 返回空結果", latency
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 2
                    print(f"    ⚠️ Rate limit，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    continue
                else:
                    return False, f"API 錯誤: {response.status_code}", latency
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return False, "請求超時", time.time() - start_time
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return False, str(e), time.time() - start_time

        return False, "達到最大重試次數", time.time() - start_time

    except ImportError:
        return False, "需要安裝 requests 套件", 0


def test_checkpoint1_cases():
    """測試 Checkpoint 1 的案例"""

    print("=" * 80)
    print("🧪 使用 Checkpoint 1 數據測試 Few-shot 方案")
    print("=" * 80)

    # 載入測試數據
    test_cases = load_checkpoint1_data()
    print(f"\n📊 載入 {len(test_cases)} 個測試案例")

    api_key = get_api_key()
    if not api_key:
        print("❌ 錯誤：找不到 GEMINI_API_KEY")
        return []

    # 選擇前 5 個案例進行測試（避免 API 限制）
    selected_cases = test_cases[:5]

    results = []

    for i, case in enumerate(selected_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"📋 Case {case['case_id']}: {case['company']['name']}")
        print("=" * 80)

        company_name = case["company"]["name"]
        registration_id = case["company"]["registration_id"]
        industry = case["industry"]["type"]
        before_text = case["before_text"]

        print(f"\n🏢 公司資訊:")
        print(f"   名稱: {company_name}")
        print(f"   統編: {registration_id}")
        print(f"   產業: {industry}")
        print(f"\n📝 原始素材預覽:")
        print(f"   {before_text[:100]}...")

        # 生成 Prompt（模擬有選填欄位的情況，測試資訊使用率）
        # 為了測試資訊使用率，我們模擬添加一些選填欄位
        test_capital = 10000000 + (i * 1000000)  # 1000萬, 1100萬, etc.
        test_employees = 50 + (i * 10)  # 50人, 60人, etc.
        test_founded_year = 2000 + i  # 2001, 2002, etc.

        prompt = build_generate_prompt(
            organ=company_name,
            organ_no=registration_id,
            user_brief=before_text,
            capital=test_capital,
            employees=test_employees,
            founded_year=test_founded_year,
            word_limit=200,
        )

        print(f"\n🔹 測試用選填欄位:")
        print(f"   資本額: {test_capital / 10000:.0f}萬元")
        print(f"   員工人數: {test_employees}人")
        print(f"   成立年份: {test_founded_year}年")

        # 調用 API
        print(f"\n🤖 正在調用 LLM API...")
        success, output, latency = call_llm_api(prompt, api_key)

        if not success:
            print(f"   ❌ API 調用失敗: {output}")
            results.append(
                {
                    "case_id": case["case_id"],
                    "company_name": company_name,
                    "success": False,
                    "error": output,
                }
            )
            continue

        print(f"   ✅ API 調用成功 (耗時: {latency:.2f}秒)")
        print(f"\n📝 生成結果:\n{output}")

        # Validation 檢查
        is_valid, missing = validate_info_usage(
            output,
            capital=test_capital,
            employees=test_employees,
            founded_year=test_founded_year,
        )

        print(f"\n🔍 Validation 結果:")
        if is_valid:
            print(f"   ✅ 通過 - 所有數字資訊都被使用")
            info_usage_rate = 100.0
        else:
            print(f"   ⚠️ 部分資訊缺失:")
            for m in missing:
                print(f"      - {m}")
            info_usage_rate = (3 - len(missing)) / 3 * 100

        print(f"   📊 資訊使用率: {info_usage_rate:.0f}%")

        results.append(
            {
                "case_id": case["case_id"],
                "company_name": company_name,
                "success": True,
                "output": output,
                "is_valid": is_valid,
                "missing": missing,
                "info_usage_rate": info_usage_rate,
                "latency": latency,
            }
        )

        # API 調用間隔
        if i < len(selected_cases):
            print(f"\n⏱️  等待 3 秒後繼續...")
            time.sleep(3)

    return results


def generate_report(results):
    """生成測試報告"""

    print("\n" + "=" * 80)
    print("📊 Checkpoint 1 數據測試報告")
    print("=" * 80)

    if not results:
        print("\n⚠️ 沒有測試結果")
        return

    # 統計
    total_tests = len(results)
    successful_api_calls = sum(1 for r in results if r.get("success", False))
    valid_outputs = sum(1 for r in results if r.get("is_valid", False))

    avg_latency = sum(r.get("latency", 0) for r in results) / len(results)
    avg_usage_rate = sum(r.get("info_usage_rate", 0) for r in results) / len(results)

    print(f"\n📈 統計數據:")
    print(f"   總測試數: {total_tests}")
    print(f"   API 成功調用: {successful_api_calls}/{total_tests}")
    print(f"   通過 Validation: {valid_outputs}/{successful_api_calls}")
    print(f"   平均響應時間: {avg_latency:.2f}秒")
    print(f"   平均資訊使用率: {avg_usage_rate:.1f}%")

    print(f"\n📋 各案例詳情:")
    for r in results:
        status = "✅" if r.get("is_valid") else ("❌" if r.get("success") else "⚠️")
        print(
            f"   {status} Case {r['case_id']} ({r['company_name']}): {r.get('info_usage_rate', 0):.0f}% 使用率"
        )
        if r.get("missing"):
            print(f"      缺失: {', '.join(r['missing'])}")

    print("\n" + "=" * 80)

    # 與舊方案對比
    print("\n📊 與舊方案對比:")
    print(f"   舊方案平均使用率: 46.7%")
    print(f"   新方案平均使用率: {avg_usage_rate:.1f}%")
    improvement = avg_usage_rate - 46.7
    print(f"   提升幅度: {improvement:+.1f}%")

    if avg_usage_rate >= 80:
        print(f"\n🎉 效果顯著！資訊使用率達到目標 (>80%)")
    elif improvement > 0:
        print(f"\n✅ 有提升，但可能需要進一步優化")
    else:
        print(f"\n⚠️ 需要檢查方案效果")

    # 保存報告
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "checkpoint1_test_data",
        "total_tests": total_tests,
        "successful_api_calls": successful_api_calls,
        "valid_outputs": valid_outputs,
        "avg_latency": avg_latency,
        "avg_usage_rate": avg_usage_rate,
        "improvement": improvement,
        "results": results,
    }

    report_path = Path(__file__).parent / "checkpoint1_fewshot_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n📁 報告已保存至: {report_path}")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🔧 Checkpoint 1 數據 + Few-shot 方案測試\n")

    # 檢查 requests
    try:
        import requests
    except ImportError:
        print("❌ 需要安裝 requests 套件: pip install requests")
        sys.exit(1)

    # 運行測試
    results = test_checkpoint1_cases()

    # 生成報告
    generate_report(results)
