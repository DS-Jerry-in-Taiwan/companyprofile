#!/usr/bin/env python3
"""
Few-shot 方案實際 API 測試
========================

使用實際 LLM API 測試 Few-shot + Validation 方案的效果

使用方法:
  export GEMINI_API_KEY=your_api_key
  python3 test_fewshot_api.py

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


def get_api_key():
    """獲取 API Key"""
    # 首先嘗試從環境變量獲取
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    # 嘗試從 .env 文件加載
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                    api_key = line.split("=", 1)[1].strip()
                    if api_key:
                        return api_key

    print("❌ 錯誤：找不到 GEMINI_API_KEY")
    print("   請確保 .env 文件存在且包含 GEMINI_API_KEY")
    sys.exit(1)


def call_llm_api(prompt, api_key, max_retries=3):
    """
    調用 Gemini API

    Args:
        prompt: 生成的 prompt
        api_key: Gemini API Key
        max_retries: 最大重試次數

    Returns:
        tuple: (success: bool, result: str, latency: float)
    """
    try:
        import requests

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        headers = {"Content-Type": "application/json"}

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800,
            },
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
                    else:
                        return False, "API 返回空結果", latency

                elif response.status_code == 429:
                    # Rate limit，等待後重試
                    wait_time = (attempt + 1) * 2
                    print(f"    ⚠️ Rate limit，等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                    continue
                else:
                    return (
                        False,
                        f"API 錯誤: {response.status_code} - {response.text}",
                        latency,
                    )

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"    ⚠️ 請求超時，重試中...")
                    time.sleep(2)
                    continue
                return False, "請求超時", time.time() - start_time

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"    ⚠️ 錯誤: {e}，重試中...")
                    time.sleep(2)
                    continue
                return False, str(e), time.time() - start_time

        return False, "達到最大重試次數", time.time() - start_time

    except ImportError:
        return False, "需要安裝 requests 套件: pip install requests", 0


def run_api_tests():
    """運行 API 測試"""

    print("=" * 80)
    print("🧪 Few-shot + Validation 方案實際 API 測試")
    print("=" * 80)

    api_key = get_api_key()

    # 測試案例
    test_cases = [
        {
            "name": "測試案例 A：完整資訊",
            "organ": "創新科技有限公司",
            "capital": 10000000,  # 1000萬
            "employees": 50,
            "founded_year": 2018,
            "word_limit": 150,
        },
        {
            "name": "測試案例 B：只有資本額",
            "organ": "大資本企業股份有限公司",
            "capital": 500000000,  # 5億
            "employees": None,
            "founded_year": None,
            "word_limit": 150,
        },
        {
            "name": "測試案例 C：只有員工人數",
            "organ": "中型企業有限公司",
            "capital": None,
            "employees": 150,
            "founded_year": None,
            "word_limit": 150,
        },
        {
            "name": "測試案例 D：只有成立年份",
            "organ": "老牌企業有限公司",
            "capital": None,
            "employees": None,
            "founded_year": 1995,
            "word_limit": 150,
        },
    ]

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"📋 {case['name']}")
        print("=" * 80)

        # 生成 Prompt
        prompt = build_generate_prompt(
            organ=case["organ"],
            capital=case.get("capital"),
            employees=case.get("employees"),
            founded_year=case.get("founded_year"),
            word_limit=case.get("word_limit"),
        )

        print(f"\n🔹 公司名稱: {case['organ']}")
        if case.get("capital"):
            print(f"   資本額: {case['capital'] / 10000:.0f}萬元")
        if case.get("employees"):
            print(f"   員工人數: {case['employees']}人")
        if case.get("founded_year"):
            print(f"   成立年份: {case['founded_year']}年")

        # 調用 API
        print(f"\n🤖 正在調用 LLM API...")
        success, output, latency = call_llm_api(prompt, api_key)

        if not success:
            print(f"   ❌ API 調用失敗: {output}")
            results.append(
                {
                    "name": case["name"],
                    "success": False,
                    "error": output,
                    "latency": latency,
                }
            )
            continue

        print(f"   ✅ API 調用成功 (耗時: {latency:.2f}秒)")
        print(f"\n📝 生成結果:\n{output}")

        # Validation 檢查
        is_valid, missing = validate_info_usage(
            output,
            capital=case.get("capital"),
            employees=case.get("employees"),
            founded_year=case.get("founded_year"),
        )

        print(f"\n🔍 Validation 結果:")
        if is_valid:
            print(f"   ✅ 通過 - 所有數字資訊都被使用")
            info_usage_rate = 100.0
        else:
            print(f"   ⚠️ 部分資訊缺失:")
            for m in missing:
                print(f"      - {m}")

            # 計算使用率
            expected_count = sum(
                [
                    1 if case.get("capital") else 0,
                    1 if case.get("employees") else 0,
                    1 if case.get("founded_year") else 0,
                ]
            )
            actual_count = expected_count - len(missing)
            info_usage_rate = (
                (actual_count / expected_count * 100) if expected_count > 0 else 100.0
            )

        print(f"   📊 資訊使用率: {info_usage_rate:.0f}%")

        results.append(
            {
                "name": case["name"],
                "success": True,
                "output": output,
                "is_valid": is_valid,
                "missing": missing,
                "info_usage_rate": info_usage_rate,
                "latency": latency,
            }
        )

        # API 調用間隔
        if i < len(test_cases):
            print(f"\n⏱️  等待 2 秒後繼續下一個測試...")
            time.sleep(2)

    return results


def generate_report(results):
    """生成測試報告"""

    print("\n" + "=" * 80)
    print("📊 測試報告總結")
    print("=" * 80)

    # 統計
    total_tests = len(results)
    successful_api_calls = sum(1 for r in results if r["success"])
    valid_outputs = sum(1 for r in results if r.get("is_valid", False))

    avg_latency = sum(r["latency"] for r in results) / len(results) if results else 0
    avg_usage_rate = (
        sum(r.get("info_usage_rate", 0) for r in results) / len(results)
        if results
        else 0
    )

    print(f"\n📈 統計數據:")
    print(f"   總測試數: {total_tests}")
    print(f"   API 成功調用: {successful_api_calls}/{total_tests}")
    print(f"   通過 Validation: {valid_outputs}/{successful_api_calls}")
    print(f"   平均響應時間: {avg_latency:.2f}秒")
    print(f"   平均資訊使用率: {avg_usage_rate:.1f}%")

    print(f"\n📋 各案例詳情:")
    for r in results:
        status = "✅" if r.get("is_valid") else ("❌" if r["success"] else "⚠️")
        print(f"   {status} {r['name']}: {r.get('info_usage_rate', 0):.0f}% 使用率")
        if r.get("missing"):
            print(f"      缺失: {', '.join(r['missing'])}")

    print("\n" + "=" * 80)

    # 與舊方案對比
    print("\n📊 與舊方案對比:")
    print(f"   舊方案平均使用率: 46.7%")
    print(f"   新方案平均使用率: {avg_usage_rate:.1f}%")
    improvement = avg_usage_rate - 46.7
    print(f"   提升幅度: {improvement:+.1f}%")

    if improvement > 20:
        print("\n🎉 效果顯著！方案成功提升資訊使用率")
    elif improvement > 0:
        print("\n✅ 有一定效果，建議進一步優化")
    else:
        print("\n⚠️ 效果不明顯，需要考慮其他方案")

    print("=" * 80)

    # 保存報告
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": total_tests,
        "successful_api_calls": successful_api_calls,
        "valid_outputs": valid_outputs,
        "avg_latency": avg_latency,
        "avg_usage_rate": avg_usage_rate,
        "improvement": improvement,
        "results": results,
    }

    report_path = Path(__file__).parent / "fewshot_api_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n📁 報告已保存至: {report_path}")


if __name__ == "__main__":
    print("\n🔧 Few-shot + Validation API 測試")
    print("注意: 需要設置 GEMINI_API_KEY 環境變量\n")

    # 檢查是否需要安裝 requests
    try:
        import requests
    except ImportError:
        print("❌ 需要安裝 requests 套件")
        print("   請執行: pip install requests")
        sys.exit(1)

    # 運行測試
    results = run_api_tests()

    # 生成報告
    generate_report(results)
