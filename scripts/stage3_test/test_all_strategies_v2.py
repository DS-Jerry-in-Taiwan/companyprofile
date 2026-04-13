"""
策略三：Gemini 規劃 + Tavily 執行
====================================

概念：
1. Gemini 產出結構化查詢框架（要查哪些欄位）
2. 依照框架，用 Tavily 批次查詢各欄位
3. 合併結果

優點：
- Gemini：聰明的規劃者，知道要查什麼
- Tavily：便宜的執行者，負責實際搜尋
"""

import os
import sys
import time
import json
import re
from datetime import datetime
from typing import Dict, Any, List

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from google import genai
from google.genai import types


# ===== Gemini：產出查詢框架 =====
GEMINI_PLANNER_PROMPT = """你是一個公司資訊搜尋規劃專家。

任務：為「{company_name}」規劃搜尋框架。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "{company_name}",
    "queries": [
        {{
            "field": "欄位名稱",
            "query": "Tavily 搜尋查詢",
            "priority": 1-3（1最高）,
            "description": "為什麼要查這個"
        }}
    ],
    "confidence": "高/中/低"
}}

【欄位定義】
- unified_number: 統一編號（8位數）
- capital: 資本額
- founded_date: 成立時間
- address: 公司地址
- officer: 負責人
- main_services: 主要產品/服務
- business_items: 營業項目（盡量詳細）

【規則】
1. 根據公司名稱，規劃最適合的搜尋關鍵字
2. 優先查高優先級欄位
3. 每個查詢要具體明確
4. 統一編號和資本額通常最重要（priority=1）

請回覆 JSON："""


# ===== Tavily 執行 =====
def tavily_batch_search(provider, queries: List[Dict]) -> Dict[str, Any]:
    """
    批次執行多個 Tavily 查詢
    """
    results = {}
    total_elapsed = 0

    for q in queries:
        field = q["field"]
        query = q["query"]
        priority = q.get("priority", 3)

        print(f"  [{priority}] {field}: {query[:40]}...")

        start = time.time()
        result = provider.get_search_info(query, max_results=2)
        elapsed = time.time() - start
        total_elapsed += elapsed

        results[field] = {
            "answer": result.get("answer", ""),
            "elapsed": elapsed,
            "raw_results": result.get("results", []),
        }

    return results, total_elapsed


# ===== 結果合併 =====
def merge_results(
    queries: List[Dict], search_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    合併搜尋結果為結構化資料
    """
    merged = {}

    for q in queries:
        field = q["field"]
        answer = search_results.get(field, {}).get("answer", "")

        # 簡單解析（可以再做複雜一點）
        if field == "unified_number":
            match = re.search(r"[0-9]{8}", answer)
            merged[field] = match.group(0) if match else answer[:20]

        elif field == "capital":
            match = re.search(r"[0-9,]+[萬億]?[元]", answer)
            merged[field] = match.group(0) if match else answer[:30]

        elif field == "founded_date":
            match = re.search(r"\d{4}年\d{1,2}月\d{1,2}日", answer)
            merged[field] = (
                match.group(0)
                if match
                else re.search(r"\d{4}年", answer).group(0)
                if re.search(r"\d{4}年", answer)
                else answer[:20]
            )

        elif field == "address":
            match = re.search(
                r"[高雄市台北市新北市台中市台南市桃園市新竹市][^。，,。\n]{5,30}",
                answer,
            )
            merged[field] = match.group(0) if match else answer[:40]

        elif field == "officer":
            match = re.search(r"負責人[：:]\s*(\S+)", answer)
            merged[field] = match.group(1) if match else answer[:10]

        else:
            merged[field] = answer[:100] if len(answer) > 100 else answer

    return merged


# ===== 主要測試函式 =====
def test_strategy_three(company_name: str = "澳霸有限公司"):
    """測試策略三：Gemini 規劃 + Tavily 執行"""

    print(f"\n{'=' * 70}")
    print(f"策 略 三：Gemini 規劃 + Tavily 執行")
    print(f"{'=' * 70}")

    # ===== Step 1: Gemini 規劃 =====
    print(f"\n📝 Step 1: Gemini 產出查詢框架...")

    api_key = os.getenv("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    planner_prompt = GEMINI_PLANNER_PROMPT.format(company_name=company_name)

    start = time.time()
    planner_response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=planner_prompt,
        config=types.GenerateContentConfig(
            tools=[search_tool],
            temperature=0.1,
        ),
    )
    planner_time = time.time() - start

    print(f"  ⏱️  規劃耗時: {planner_time:.2f}s")

    # 解析 JSON
    json_str = re.search(
        r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", planner_response.text, re.DOTALL
    )

    if json_str:
        try:
            query_framework = json.loads(json_str.group(0))
            print(f"\n  📋 查詢框架:")
            print(f"      公司: {query_framework.get('company_name', 'N/A')}")
            print(f"      信心度: {query_framework.get('confidence', 'N/A')}")
            print(f"      查詢數量: {len(query_framework.get('queries', []))}")

            for q in query_framework.get("queries", []):
                print(
                    f"        [{q.get('priority', '?')}] {q.get('field')}: {q.get('query', '')[:30]}..."
                )

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 解析失敗: {e}")
            query_framework = None
    else:
        print(f"  ❌ 無法提取 JSON")
        query_framework = None

    if not query_framework:
        return None

    # ===== Step 2: Tavily 批次執行 =====
    print(f"\n📝 Step 2: Tavily 批次執行...")

    from src.services.tavily_search import TavilySearchProvider

    tavily_provider = TavilySearchProvider()

    queries = query_framework.get("queries", [])

    start = time.time()
    search_results, search_time = tavily_batch_search(tavily_provider, queries)
    total_time = planner_time + search_time

    print(f"\n  ⏱️  搜尋耗時: {search_time:.2f}s")
    print(f"  ⏱️  總耗時: {total_time:.2f}s")

    # ===== Step 3: 合併結果 =====
    print(f"\n📝 Step 3: 合併結果...")

    merged = merge_results(queries, search_results)

    print(f"\n  📊 結構化結果:")
    for field, value in merged.items():
        print(
            f"      {field}: {value[:50]}..."
            if len(str(value)) > 50
            else f"      {field}: {value}"
        )

    return {
        "strategy": "gemini_planner_tavily_executor",
        "company_name": company_name,
        "query_framework": query_framework,
        "search_results": search_results,
        "merged_result": merged,
        "elapsed_times": {
            "planner": planner_time,
            "search": search_time,
            "total": total_time,
        },
        "api_calls": 1 + len(queries),  # 1 for planner + N for searches
    }


def test_all_strategies(company_name: str = "澳霸有限公司"):
    """測試所有三種策略"""

    print("=" * 70)
    print("搜 尋 策 略 全 面 比 較")
    print("=" * 70)
    print(f"\n測試公司: {company_name}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # ===== 策略一：Tavily 批次 =====
    print(f"\n{'=' * 70}")
    print(f"策 略 一：Tavily 批次搜尋")
    print(f"{'=' * 70}")

    from src.services.tavily_search import TavilySearchProvider

    tavily_provider = TavilySearchProvider()

    start = time.time()
    tavily_batch_result = tavily_provider.get_search_info(
        f"{company_name} 統一編號 資本額 成立時間 地址 負責人 主要服務 營業項目",
        max_results=3,
    )
    tavily_batch_time = time.time() - start

    results["tavily_batch"] = {
        "success": True,
        "elapsed": tavily_batch_time,
        "api_calls": 1,
        "answer": tavily_batch_result.get("answer", ""),
        "answer_length": len(tavily_batch_result.get("answer", "")),
    }

    print(f"\n  ⏱️  耗時: {tavily_batch_time:.2f}s")
    print(f"  📝 Answer ({len(tavily_batch_result.get('answer', ''))} 字):")
    print(f"    {tavily_batch_result.get('answer', '')}")

    # ===== 策略二：Gemini Few-shot =====
    print(f"\n{'=' * 70}")
    print(f"策 略 二：Gemini Few-shot + Validate")
    print(f"{'=' * 70}")

    from google import genai
    from google.genai import types

    GEMINI_PROMPT = f"""你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "公司名稱",
    "unified_number": "統一編號",
    "capital": "資本額",
    "founded_date": "成立時間",
    "address": "公司地址",
    "officer": "負責人",
    "main_services": "主要服務",
    "business_items": "營業項目"
}}

請搜尋並回覆 JSON。"""

    api_key = os.getenv("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    start = time.time()
    gemini_response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=GEMINI_PROMPT,
        config=types.GenerateContentConfig(
            tools=[search_tool],
            temperature=0.2,
        ),
    )
    gemini_time = time.time() - start

    json_match = re.search(
        r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", gemini_response.text, re.DOTALL
    )

    results["gemini_fewshot"] = {
        "success": True,
        "elapsed": gemini_time,
        "api_calls": 1,
        "answer": gemini_response.text,
        "answer_length": len(gemini_response.text),
        "json_parsed": json_match.group(0) if json_match else None,
    }

    print(f"\n  ⏱️  耗時: {gemini_time:.2f}s")
    print(f"  📝 Answer ({len(gemini_response.text)} 字)")

    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            print(f"  ✅ JSON 解析成功")
            for k, v in parsed.items():
                print(f"      {k}: {str(v)[:40]}...")
        except:
            print(f"  ⚠️ JSON 解析失敗")

    # ===== 策略三：Gemini 規劃 + Tavily 執行 =====
    print(f"\n{'=' * 70}")
    print(f"策 略 三：Gemini 規劃 + Tavily 執行（新架構）")
    print(f"{'=' * 70}")

    strategy_three_result = test_strategy_three(company_name)

    if strategy_three_result:
        results["gemini_tavily_hybrid"] = strategy_three_result

    # ===== 比較總結 =====
    print(f"\n{'=' * 70}")
    print(f"比 較 總 結")
    print(f"{'=' * 70}")

    print(f"\n📊 耗時比較:")
    print(
        f"  策略一（Tavily 批次）:       {results['tavily_batch']['elapsed']:.2f}s ({results['tavily_batch']['api_calls']} 次 API)"
    )
    print(
        f"  策略二（Gemini Few-shot）:   {results['gemini_fewshot']['elapsed']:.2f}s ({results['gemini_fewshot']['api_calls']} 次 API)"
    )
    if results.get("gemini_tavily_hybrid"):
        str3 = results["gemini_tavily_hybrid"]
        print(
            f"  策略三（Gemini+Tavily）:   {str3['elapsed_times']['total']:.2f}s ({str3['api_calls']} 次 API)"
        )

    print(f"\n📊 資訊長度:")
    print(f"  策略一: {results['tavily_batch']['answer_length']} 字")
    print(f"  策略二: {results['gemini_fewshot']['answer_length']} 字")
    if results.get("gemini_tavily_hybrid"):
        total_len = sum(
            len(str(v))
            for v in results["gemini_tavily_hybrid"]["merged_result"].values()
        )
        print(f"  策略三: {total_len} 字（結構化）")

    print(f"\n📊 格式品質:")
    print(f"  策略一: 自然語言，需要解析 ❌")
    print(f"  策略二: JSON 格式，直接可用 ✅")
    print(f"  策略三: 結構化欄位，直接可用 ✅")

    print(f"\n💡 推薦:")
    if results.get("gemini_tavily_hybrid"):
        str3 = results["gemini_tavily_hybrid"]
        if str3["elapsed_times"]["total"] < results["gemini_fewshot"]["elapsed"]:
            print(
                f"  → 速度優先：策略三（Gemini+Tavily）- 快 {results['gemini_fewshot']['elapsed'] - str3['elapsed_times']['total']:.2f}s"
            )
    print(f"  → 資訊完整：策略二（Gemini Few-shot）")

    # 儲存結果
    output_path = os.path.join(
        PROJECT_ROOT, "scripts", "stage3_test", "all_strategies_v2.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n\n📁 完整結果已儲存至: {output_path}")

    return results


if __name__ == "__main__":
    test_all_strategies("澳霸有限公司")
