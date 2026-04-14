"""
不同模型效能比較測試
====================

比較不同模型的公司搜尋效能：
1. gemini-2.0-flash (預設)
2. gemini-1.5-flash
3. gemini-2.0-flash-lite
4. gpt-4o-mini (如果可用)
"""

import os
import sys
import time
import json
import statistics

# 設定路徑
_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


# 測試設定
TEST_COMPANY = "私立揚才文理短期補習班"
ITERATIONS = 3


def test_gemini_flash():
    """測試 gemini-2.0-flash"""
    from google import genai
    from google.genai import types

    times = []

    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    prompt = f"""你是一個公司資訊搜尋專家。請搜尋「{TEST_COMPANY}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "公司名稱",
    "unified_number": "統一編號",
    "capital": "資本額",
    "founded_date": "成立時間",
    "address": "公司地址",
    "officer": "負責人",
    "main_services": "主要服務"
}}

請搜尋並回覆 JSON。"""

    for i in range(ITERATIONS):
        start = time.time()
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool],
                temperature=0.2,
            ),
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  [{i + 1}/{ITERATIONS}] gemini-2.0-flash: {elapsed:.2f}s")

    return times, response.text


def test_gemini_15_flash():
    """測試 gemini-1.5-flash"""
    from google import genai
    from google.genai import types

    times = []

    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    prompt = f"""你是一個公司資訊搜尋專家。請搜尋「{TEST_COMPANY}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "公司名稱",
    "unified_number": "統一編號",
    "capital": "資本額",
    "founded_date": "成立時間",
    "address": "公司地址",
    "officer": "負責人",
    "main_services": "主要服務"
}}

請搜尋並回覆 JSON。"""

    for i in range(ITERATIONS):
        try:
            start = time.time()
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[search_tool],
                    temperature=0.2,
                ),
            )
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  [{i + 1}/{ITERATIONS}] gemini-1.5-flash: {elapsed:.2f}s")
        except Exception as e:
            print(f"  [{i + 1}/{ITERATIONS}] gemini-1.5-flash: 失敗 - {e}")
            times.append(None)

    return [t for t in times if t is not None], response.text if times else ""


def test_gemini_flash_lite():
    """測試 gemini-2.0-flash-lite"""
    from google import genai
    from google.genai import types

    times = []

    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    prompt = f"""你是一個公司資訊搜尋專家。請搜尋「{TEST_COMPANY}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "公司名稱",
    "unified_number": "統一編號",
    "capital": "資本額",
    "founded_date": "成立時間",
    "address": "公司地址",
    "officer": "負責人",
    "main_services": "主要服務"
}}

請搜尋並回覆 JSON。"""

    for i in range(ITERATIONS):
        try:
            start = time.time()
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[search_tool],
                    temperature=0.2,
                ),
            )
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  [{i + 1}/{ITERATIONS}] gemini-2.0-flash-lite: {elapsed:.2f}s")
        except Exception as e:
            print(f"  [{i + 1}/{ITERATIONS}] gemini-2.0-flash-lite: 失敗 - {e}")
            times.append(None)

    return [t for t in times if t is not None], response.text if times else ""


def test_gpt_4o_mini():
    """測試 gpt-4o-mini"""
    from openai import OpenAI

    times = []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("  OPENAI_API_KEY 未設定，跳過測試")
        return [], ""

    client = OpenAI(api_key=api_key)

    prompt = f"""你是一個公司資訊搜尋專家。請搜尋「{TEST_COMPANY}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "公司名稱",
    "unified_number": "統一編號",
    "capital": "資本額",
    "founded_date": "成立時間",
    "address": "公司地址",
    "officer": "負責人",
    "main_services": "主要服務"
}}

請搜尋並回覆 JSON。"""

    for i in range(ITERATIONS):
        try:
            start = time.time()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一個公司資訊搜尋專家。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            elapsed = time.time() - start
            times.append(elapsed)
            result = response.choices[0].message.content
            print(f"  [{i + 1}/{ITERATIONS}] gpt-4o-mini: {elapsed:.2f}s")
        except Exception as e:
            print(f"  [{i + 1}/{ITERATIONS}] gpt-4o-mini: 失敗 - {e}")
            times.append(None)

    return [t for t in times if t is not None], result if times else ""


def test_gemini_flash_no_json():
    """測試 gemini-2.0-flash（不使用 JSON 格式，只用文字）"""
    from google import genai
    from google.genai import types

    times = []

    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    prompt = f"""請搜尋「{TEST_COMPANY}」的詳細資訊，並用一段話回覆，包含：
- 公司名稱
- 統一編號
- 成立時間
- 資本額
- 主要服務

請用中文回答。"""

    for i in range(ITERATIONS):
        start = time.time()
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool],
                temperature=0.2,
            ),
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  [{i + 1}/{ITERATIONS}] gemini-2.0-flash (無JSON): {elapsed:.2f}s")

    return times, response.text


def main():
    print("=" * 60)
    print("不同模型效能比較測試")
    print("=" * 60)
    print(f"測試公司: {TEST_COMPANY}")
    print(f"測試次數: {ITERATIONS}")
    print()

    results = {}

    # 測試 1: gemini-2.0-flash
    print("[1/5] gemini-2.0-flash (預設)")
    try:
        times, response = test_gemini_flash()
        if times:
            results["gemini-2.0-flash"] = {
                "times": times,
                "avg": statistics.mean(times),
                "min": min(times),
                "max": max(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0,
                "response": response[:200],
            }
            print(f"  平均: {statistics.mean(times):.2f}s")
    except Exception as e:
        print(f"  失敗: {e}")
    print()

    # 測試 2: gemini-1.5-flash
    print("[2/5] gemini-1.5-flash")
    try:
        times, response = test_gemini_15_flash()
        if times:
            results["gemini-1.5-flash"] = {
                "times": times,
                "avg": statistics.mean(times),
                "min": min(times),
                "max": max(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0,
                "response": response[:200],
            }
            print(f"  平均: {statistics.mean(times):.2f}s")
    except Exception as e:
        print(f"  失敗: {e}")
    print()

    # 測試 3: gemini-2.0-flash-lite
    print("[3/5] gemini-2.0-flash-lite")
    try:
        times, response = test_gemini_flash_lite()
        if times:
            results["gemini-2.0-flash-lite"] = {
                "times": times,
                "avg": statistics.mean(times),
                "min": min(times),
                "max": max(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0,
                "response": response[:200],
            }
            print(f"  平均: {statistics.mean(times):.2f}s")
    except Exception as e:
        print(f"  失敗: {e}")
    print()

    # 測試 4: gpt-4o-mini
    print("[4/5] gpt-4o-mini")
    try:
        times, response = test_gpt_4o_mini()
        if times:
            results["gpt-4o-mini"] = {
                "times": times,
                "avg": statistics.mean(times),
                "min": min(times),
                "max": max(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0,
                "response": response[:200],
            }
            print(f"  平均: {statistics.mean(times):.2f}s")
    except Exception as e:
        print(f"  失敗: {e}")
    print()

    # 測試 5: gemini-2.0-flash (無 JSON)
    print("[5/5] gemini-2.0-flash (不使用 JSON 格式)")
    try:
        times, response = test_gemini_flash_no_json()
        if times:
            results["gemini-2.0-flash (無JSON)"] = {
                "times": times,
                "avg": statistics.mean(times),
                "min": min(times),
                "max": max(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0,
                "response": response[:200],
            }
            print(f"  平均: {statistics.mean(times):.2f}s")
    except Exception as e:
        print(f"  失敗: {e}")
    print()

    # 結果總結
    print("=" * 60)
    print("結果總結")
    print("=" * 60)

    if not results:
        print("沒有成功的測試結果")
        return

    # 排序
    sorted_results = sorted(results.items(), key=lambda x: x[1]["avg"])

    # 找基準（最快的）
    fastest_name, fastest_data = sorted_results[0]
    fastest_avg = fastest_data["avg"]

    print(
        f"\n{'模型':<30} {'平均':<10} {'最小':<10} {'最大':<10} {'標準差':<10} {'vs最快':<10}"
    )
    print("-" * 80)

    for name, data in sorted_results:
        vs_fastest = (
            ((data["avg"] - fastest_avg) / fastest_avg * 100) if fastest_avg > 0 else 0
        )
        marker = (
            "✅" if data["avg"] == fastest_avg else ("✅" if vs_fastest < 10 else "⚠️")
        )
        print(
            f"{name:<30} {data['avg']:<10.2f} {data['min']:<10.2f} {data['max']:<10.2f} {data['stdev']:<10.2f} {vs_fastest:>+7.1f}% {marker}"
        )

    print()
    print("=" * 60)
    print("結論")
    print("=" * 60)

    if fastest_name == "gemini-2.0-flash":
        print(f"最快的模型: {fastest_name} ({fastest_avg:.2f}s)")
        print("預設模型已經是最快的選項。")
    else:
        print(f"最快的模型: {fastest_name} ({fastest_avg:.2f}s)")
        print(
            f"比 gemini-2.0-flash 快 {((results['gemini-2.0-flash']['avg'] - fastest_avg) / results['gemini-2.0-flash']['avg'] * 100):.1f}%"
        )

    # 儲存結果
    with open(
        os.path.join(os.path.dirname(__file__), "model_comparison_results.json"), "w"
    ) as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n詳細結果已儲存至: model_comparison_results.json")


if __name__ == "__main__":
    main()
