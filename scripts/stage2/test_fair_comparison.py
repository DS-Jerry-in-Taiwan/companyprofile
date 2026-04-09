#!/usr/bin/env python3
"""
公平比較測試：舊 Prompt vs 新 Prompt (Few-shot)
================================================

比較相同條件下（都無網絡搜索）的生成時間差異

使用方法:
  python3 test_fair_comparison.py

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
from prompt_builder import build_generate_prompt


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


def call_llm_api(prompt, api_key):
    """調用 Gemini API"""
    import requests

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800},
    }

    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    latency = time.time() - start_time

    if response.status_code == 200:
        data = response.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            result = data["candidates"][0]["content"]["parts"][0]["text"]
            return True, result.strip(), latency
    return False, f"API Error: {response.status_code}", latency


def build_old_prompt(
    organ, capital=None, employees=None, founded_year=None, word_limit=200
):
    """構建舊版 Prompt（無 Few-shot）"""
    sections = []

    sections.append(f"## 公司基本資訊")
    sections.append(f"公司名稱：{organ}")
    if capital:
        capital_wan = capital / 10000
        if capital_wan >= 10000:
            sections.append(f"資本額：{capital_wan / 10000:.2f} 億元")
        else:
            sections.append(f"資本額：{capital_wan:.0f} 萬元")
    if employees:
        sections.append(f"員工人數：約 {employees} 人")
    if founded_year:
        sections.append(f"成立年份：西元 {founded_year} 年")

    sections.append(f"\n## 輸出要求")
    sections.append(
        f"請根據上述資訊，生成一段專業的公司簡介（不超過 {word_limit} 字）。"
    )

    # 舊版只有簡單要求，無 Few-shot
    if capital or employees or founded_year:
        sections.append(f"\n### 重要提示")
        sections.append("請確保使用上述提供的資本額、員工人數和成立年份資訊。")

    return "\n".join(sections)


def compare_prompts():
    """比較舊版和新版 Prompt"""

    print("=" * 80)
    print("⚖️  公平比較測試：舊 Prompt vs 新 Prompt (Few-shot)")
    print("=" * 80)
    print("\n注意：此測試比較純 LLM 生成時間（無網絡搜索）\n")

    api_key = get_api_key()
    if not api_key:
        print("❌ 找不到 API Key")
        return

    # 測試參數
    test_cases = [
        {
            "name": "測試 1: 完整資訊",
            "organ": "測試科技有限公司",
            "capital": 10000000,
            "employees": 50,
            "founded_year": 2018,
        },
        {
            "name": "測試 2: 只有資本額",
            "organ": "資本公司",
            "capital": 50000000,
            "employees": None,
            "founded_year": None,
        },
    ]

    results = []

    for case in test_cases:
        print(f"\n{'=' * 80}")
        print(f"📋 {case['name']}")
        print("=" * 80)

        # 構建舊版 Prompt
        old_prompt = build_old_prompt(
            case["organ"],
            capital=case.get("capital"),
            employees=case.get("employees"),
            founded_year=case.get("founded_year"),
        )

        # 構建新版 Prompt (Few-shot)
        new_prompt = build_generate_prompt(
            case["organ"],
            capital=case.get("capital"),
            employees=case.get("employees"),
            founded_year=case.get("founded_year"),
            word_limit=200,
        )

        # 統計 token 數量（簡單估算：字符數 / 4）
        old_tokens = len(old_prompt) // 4
        new_tokens = len(new_prompt) // 4

        print(f"\n📊 Prompt 大小比較:")
        print(f"   舊版: {len(old_prompt)} 字符 (~{old_tokens} tokens)")
        print(f"   新版: {len(new_prompt)} 字符 (~{new_tokens} tokens)")
        print(
            f"   差異: +{len(new_prompt) - len(old_prompt)} 字符 (+{new_tokens - old_tokens} tokens)"
        )

        # 測試舊版 (運行 3 次取平均)
        print(f"\n🔄 測試舊版 Prompt (3 次)...")
        old_times = []
        for i in range(3):
            success, _, latency = call_llm_api(old_prompt, api_key)
            if success:
                old_times.append(latency)
                print(f"   第 {i + 1} 次: {latency:.2f}s")
            time.sleep(1)

        old_avg = sum(old_times) / len(old_times) if old_times else 0
        print(f"   平均: {old_avg:.2f}s")

        # 測試新版
        print(f"\n🔄 測試新版 Prompt (3 次)...")
        new_times = []
        for i in range(3):
            success, _, latency = call_llm_api(new_prompt, api_key)
            if success:
                new_times.append(latency)
                print(f"   第 {i + 1} 次: {latency:.2f}s")
            time.sleep(1)

        new_avg = sum(new_times) / len(new_times) if new_times else 0
        print(f"   平均: {new_avg:.2f}s")

        # 比較結果
        diff = new_avg - old_avg
        diff_pct = (diff / old_avg * 100) if old_avg > 0 else 0

        print(f"\n📈 比較結果:")
        print(f"   舊版平均: {old_avg:.2f}s")
        print(f"   新版平均: {new_avg:.2f}s")
        print(f"   差異: {diff:+.2f}s ({diff_pct:+.1f}%)")

        if diff > 0.5:
            print(f"   ⚠️  新版明顯較慢 (+{diff:.2f}s)")
        elif diff < -0.5:
            print(f"   ⚡ 新版明顯較快 ({diff:.2f}s)")
        else:
            print(f"   ✅ 差異很小，可忽略不計")

        results.append(
            {
                "name": case["name"],
                "old_avg": old_avg,
                "new_avg": new_avg,
                "diff": diff,
                "diff_pct": diff_pct,
                "old_tokens": old_tokens,
                "new_tokens": new_tokens,
            }
        )

        if case != test_cases[-1]:
            print(f"\n⏱️  等待 3 秒...")
            time.sleep(3)

    # 總結
    print("\n" + "=" * 80)
    print("📊 測試總結")
    print("=" * 80)

    for r in results:
        print(f"\n{r['name']}:")
        print(f"   舊版: {r['old_avg']:.2f}s ({r['old_tokens']} tokens)")
        print(f"   新版: {r['new_avg']:.2f}s ({r['new_tokens']} tokens)")
        print(f"   差異: {r['diff']:+.2f}s ({r['diff_pct']:+.1f}%)")

    avg_diff = sum(r["diff"] for r in results) / len(results)
    print(f"\n📈 平均時間差異: {avg_diff:+.2f}s")

    if avg_diff > 0:
        print(f"\n⚠️  新版 Prompt 比舊版慢約 {avg_diff:.2f} 秒")
        print("   這是因為 Few-shot 範例增加了 token 數量")
    else:
        print(f"\n⚡ 新版 Prompt 比舊版快約 {abs(avg_diff):.2f} 秒")

    print("\n" + "=" * 80)
    print("📝 說明:")
    print("   之前報告的 '5.43s → 1.33s' 比較是不正確的")
    print("   因為舊測試包含了網絡搜索，而新測試沒有")
    print("   在相同條件下（都無搜索），新版應該略慢於舊版")
    print("=" * 80)


if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("❌ 需要安裝 requests: pip install requests")
        sys.exit(1)

    compare_prompts()
