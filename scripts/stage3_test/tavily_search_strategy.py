"""
Tavily 搜尋策略比較實驗
===========================

目標：比較不同搜尋策略的效率與資訊品質

策略：
1. 批次搜尋 - 一次問多個欄位
2. 逐項搜尋 - 每個欄位分開搜
3. 混合模式 - 先批次後逐項

"""

import os
import sys
import time
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.services.tavily_search import TavilySearchProvider


# ===== 結構化欄位定義 =====
STRUCTURED_FIELDS = {
    "unified_number": "統一編號（8位數字）",
    "capital": "資本額（新台幣）",
    "founded_date": "成立時間/日期",
    "address": "公司地址",
    "officer": "負責人/代表人",
    "main_services": "主要產品/服務",
    "business_items": "營業項目",
}


def strategy_batch(tavily_provider, company_name: str):
    """
    策略一：批次搜尋
    一次問多個欄位
    """
    print(f"\n{'=' * 60}")
    print(f"策略一：批次搜尋")
    print(f"{'=' * 60}")

    # 組合成一個大 query
    fields_query = "、".join(STRUCTURED_FIELDS.values())
    query = f"{company_name} 的 {fields_query}"

    print(f"Query: {query}")
    print(f"預計取得: {len(STRUCTURED_FIELDS)} 個欄位")

    start = time.time()
    result = tavily_provider.get_search_info(query, max_results=3)
    elapsed = time.time() - start

    print(f"\n⏱️  耗時: {elapsed:.2f} 秒")
    print(f"Answer 長度: {len(result.get('answer', ''))} 字")

    # 評估資訊完整性
    answer = result.get("answer", "")
    found_fields = []
    missing_fields = []

    for field_key, field_name in STRUCTURED_FIELDS.items():
        # 簡單關鍵字檢查
        if field_key == "unified_number" and (
            "42965130" in answer or "統一編號" in answer
        ):
            found_fields.append(field_key)
        elif field_key == "capital" and ("5,000,000" in answer or "資本" in answer):
            found_fields.append(field_key)
        elif field_key == "founded_date" and ("2018" in answer or "成立" in answer):
            found_fields.append(field_key)
        elif field_key == "address" and (
            "高雄" in answer or "鼓山" in answer or "地址" in answer
        ):
            found_fields.append(field_key)
        elif field_key == "officer" and ("紀竹祐" in answer or "負責人" in answer):
            found_fields.append(field_key)
        elif field_key == "main_services" and (
            "景觀" in answer or "綠化" in answer or "服務" in answer
        ):
            found_fields.append(field_key)
        elif field_key == "business_items" and len(answer) > 200:
            found_fields.append(field_key)  # 假設長內容有營業項目
        else:
            missing_fields.append(field_key)

    print(f"\n📊 資訊完整性:")
    print(f"  找到: {len(found_fields)}/{len(STRUCTURED_FIELDS)}")
    for f in found_fields:
        print(f"    ✅ {f}")
    for f in missing_fields:
        print(f"    ❌ {f}")

    print(f"\n📋 Answer 內容:")
    print(f"  {answer[:300]}...")

    return {
        "strategy": "batch",
        "query": query,
        "elapsed": elapsed,
        "answer_length": len(answer),
        "found_fields": found_fields,
        "missing_fields": missing_fields,
        "answer": answer,
    }


def strategy_sequential(tavily_provider, company_name: str):
    """
    策略二：逐項搜尋
    每個欄位分開搜
    """
    print(f"\n{'=' * 60}")
    print(f"策略二：逐項搜尋")
    print(f"{'=' * 60}")

    results = {}
    total_elapsed = 0
    found_count = 0

    for field_key, field_name in STRUCTURED_FIELDS.items():
        query = f"{company_name} {field_name}"
        print(f"\n[{field_key}] {field_name}")
        print(f"  Query: {query}")

        start = time.time()
        result = tavily_provider.get_search_info(query, max_results=2)
        elapsed = time.time() - start
        total_elapsed += elapsed

        answer = result.get("answer", "")
        results[field_key] = {
            "answer": answer,
            "elapsed": elapsed,
            "has_info": len(answer) > 50,
        }

        if len(answer) > 50:
            found_count += 1
            print(f"  ✅ 有資訊 ({len(answer)} 字, {elapsed:.2f}s)")
            print(f"     {answer[:100]}...")
        else:
            print(f"  ⚠️ 資訊較少 ({len(answer)} 字, {elapsed:.2f}s)")

    print(f"\n⏱️  總耗時: {total_elapsed:.2f} 秒")
    print(f"📊 資訊完整性: {found_count}/{len(STRUCTURED_FIELDS)}")

    # 合併所有 answer
    combined_answer = "\n\n".join(
        [f"【{k}】{v['answer']}" for k, v in results.items() if v["has_info"]]
    )

    return {
        "strategy": "sequential",
        "total_elapsed": total_elapsed,
        "per_field_times": {k: v["elapsed"] for k, v in results.items()},
        "found_count": found_count,
        "results": results,
        "combined_answer": combined_answer,
    }


def strategy_hybrid(tavily_provider, company_name: str):
    """
    策略三：混合模式
    步驟1: 批次取得基本資訊
    步驟2: 針對缺失的欄位逐項補充
    """
    print(f"\n{'=' * 60}")
    print(f"策略三：混合模式")
    print(f"{'=' * 60}")

    # Step 1: 批次取得基本資訊
    print(f"\n📝 Step 1: 批次取得基本資訊...")
    basic_query = f"{company_name} 統一編號、資本額、成立時間、地址、負責人"

    start = time.time()
    result = tavily_provider.get_search_info(basic_query, max_results=3)
    step1_elapsed = time.time() - start

    answer = result.get("answer", "")
    print(f"  ⏱️  耗時: {step1_elapsed:.2f} 秒")
    print(f"  📋 Answer: {answer[:200]}...")

    # Step 2: 檢查缺失並補充
    print(f"\n📝 Step 2: 檢查並補充缺失欄位...")

    # 簡單判斷缺失
    needs_detail = []
    if len(answer) < 200:
        needs_detail.append("business_items")
    if "服務" not in answer and "產品" not in answer:
        needs_detail.append("main_services")

    supplement_results = {}
    supplement_time = 0

    for field_key in needs_detail:
        query = f"{company_name} {STRUCTURED_FIELDS[field_key]}"
        print(f"  補充 [{field_key}]...")

        start = time.time()
        result = tavily_provider.get_search_info(query, max_results=2)
        elapsed = time.time() - start
        supplement_time += elapsed

        supplement_results[field_key] = {
            "answer": result.get("answer", ""),
            "elapsed": elapsed,
        }
        print(f"    ✅ {elapsed:.2f}s")

    total_elapsed = step1_elapsed + supplement_time

    print(f"\n⏱️  總耗時: {total_elapsed:.2f} 秒")
    print(f"  - 基本查詢: {step1_elapsed:.2f}s")
    print(f"  - 補充查詢: {supplement_time:.2f}s")

    # 合併結果
    combined_answer = answer
    for field_key, field_result in supplement_results.items():
        combined_answer += f"\n\n【補充-{field_key}】{field_result['answer']}"

    return {
        "strategy": "hybrid",
        "step1_elapsed": step1_elapsed,
        "supplement_time": supplement_time,
        "total_elapsed": total_elapsed,
        "supplement_results": supplement_results,
        "combined_answer": combined_answer,
    }


def cost_analysis():
    """
    費用分析（基於 Tavily 定价）
    """
    print(f"\n{'=' * 60}")
    print(f"費用分析（Tavily API 定價）")
    print(f"{'=' * 60}")

    # Tavily 定價（簡化估算）
    # Basic plan: $5/月, 1000 searches/month
    # Pro plan: $25/月, 5000 searches/month

    cost_per_search = 0.001  # $0.001 per search (估算)

    print(f"\n策略一（批次搜尋）:")
    print(f"  搜尋次數: 1 次")
    print(f"  估算費用: ${cost_per_search * 1:.4f}")

    print(f"\n策略二（逐項搜尋）:")
    print(f"  搜尋次數: {len(STRUCTURED_FIELDS)} 次")
    print(f"  估算費用: ${cost_per_search * len(STRUCTURED_FIELDS):.4f}")

    print(f"\n策略三（混合模式）:")
    print(f"  搜尋次數: 1-3 次（基本 + 補充）")
    print(f"  估算費用: ${cost_per_search * 3:.4f}")

    print(f"\n💡 建議:")
    print(f"  - 如果速度優先 → 策略一（批次）")
    print(f"  - 如果資訊完整優先 → 策略二（逐項）")
    print(f"  - 平衡速度與完整 → 策略三（混合）")


def main():
    print("=" * 60)
    print("Tavily 搜尋策略比較實驗")
    print("=" * 60)

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key == "dummy_value":
        print("❌ Tavily API Key 無效")
        return

    tavily_provider = TavilySearchProvider(api_key=api_key)

    company_name = "澳霸有限公司"
    print(f"\n測試公司: {company_name}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 測試三種策略
    result_batch = strategy_batch(tavily_provider, company_name)

    result_sequential = strategy_sequential(tavily_provider, company_name)

    result_hybrid = strategy_hybrid(tavily_provider, company_name)

    # 費用分析
    cost_analysis()

    # ===== 比較總結 =====
    print(f"\n{'=' * 60}")
    print(f"策 略 比 較 總 結")
    print(f"{'=' * 60}")

    print(f"\n📊 耗時比較:")
    print(f"  策略一（批次）: {result_batch['elapsed']:.2f}s")
    print(f"  策略二（逐項）: {result_sequential['total_elapsed']:.2f}s")
    print(f"  策略三（混合）: {result_hybrid['total_elapsed']:.2f}s")

    print(f"\n📊 資訊完整性:")
    print(
        f"  策略一（批次）: {len(result_batch['found_fields'])}/{len(STRUCTURED_FIELDS)} 欄位"
    )
    print(
        f"  策略二（逐項）: {result_sequential['found_count']}/{len(STRUCTURED_FIELDS)} 欄位"
    )

    # 儲存結果
    output = {
        "company_name": company_name,
        "timestamp": datetime.now().isoformat(),
        "structured_fields": STRUCTURED_FIELDS,
        "results": {
            "batch": result_batch,
            "sequential": result_sequential,
            "hybrid": result_hybrid,
        },
    }

    output_path = os.path.join(
        PROJECT_ROOT, "scripts", "stage3_test", "tavily_strategy_comparison.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n\n📁 完整結果已儲存至: {output_path}")


if __name__ == "__main__":
    main()
