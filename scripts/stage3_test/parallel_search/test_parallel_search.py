"""
平行搜尋測試腳本
================

測試內容：
1. 平行搜尋工具功能測試
2. 平行 vs 順序執行效能比較
3. 多源交叉驗證效果

測試公司：
- 私立揚才文理短期補習班
- 台積電
- 鴻海
"""

import os
import sys
import json
import time

# 設定路徑
_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)

from parallel_search_tool import (
    parallel_search,
    ParallelMultiSourceTool,
    TavilySearchTool,
    GeminiSearchTool,
    SearchResult,
)


# ===== 測試資料 =====
TEST_COMPANIES = [
    "私立揚才文理短期補習班",
    # "台積電",
    # "鴻海",
]


# ===== 測試函式 =====
def test_parallel_search(query: str) -> dict:
    """測試平行搜尋"""
    print(f"\n{'=' * 50}")
    print(f"測試：平行搜尋")
    print(f"{'=' * 50}")
    print(f"公司：{query}")

    start = time.time()
    result = parallel_search(query, sources=["tavily", "gemini_fewshot"])
    elapsed = time.time() - start

    return {
        "query": query,
        "tool_type": result.tool_type,
        "success": result.success,
        "elapsed_time": result.elapsed_time,
        "total_time": elapsed,
        "api_calls": result.api_calls,
        "confidence": result.data.get("_confidence", 0),
        "sources_count": result.data.get("_sources_count", 0),
        "sources": result.data.get("_sources", []),
        "elapsed_breakdown": result.data.get("_elapsed_breakdown", {}),
        "errors": result.data.get("_errors", []),
    }


def test_sequential_search(query: str) -> dict:
    """測試順序搜尋（Tavily -> Gemini）"""
    print(f"\n{'=' * 50}")
    print(f"測試：順序搜尋")
    print(f"{'=' * 50}")
    print(f"公司：{query}")

    results = {}
    total_elapsed = 0

    # Tavily
    print("\n📤 執行 Tavily...")
    start = time.time()
    try:
        tavily_tool = TavilySearchTool()
        tavily_result = tavily_tool.search(query)
        tavily_elapsed = time.time() - start
        results["tavily"] = {
            "success": tavily_result.success,
            "elapsed_time": tavily_result.elapsed_time,
            "api_calls": tavily_result.api_calls,
        }
        total_elapsed += tavily_result.elapsed_time
        print(f"   ✅ Tavily 完成，耗時 {tavily_result.elapsed_time:.2f}s")
    except Exception as e:
        results["tavily"] = {"success": False, "error": str(e)}
        print(f"   ❌ Tavily 失敗: {e}")

    # Gemini
    print("\n📤 執行 Gemini...")
    start = time.time()
    try:
        gemini_tool = GeminiSearchTool()
        gemini_result = gemini_tool.search(query)
        gemini_elapsed = time.time() - start
        results["gemini"] = {
            "success": gemini_result.success,
            "elapsed_time": gemini_result.elapsed_time,
            "api_calls": gemini_result.api_calls,
        }
        total_elapsed += gemini_result.elapsed_time
        print(f"   ✅ Gemini 完成，耗時 {gemini_result.elapsed_time:.2f}s")
    except Exception as e:
        results["gemini"] = {"success": False, "error": str(e)}
        print(f"   ❌ Gemini 失敗: {e}")

    return {
        "query": query,
        "results": results,
        "total_elapsed": total_elapsed,
        "sum_of_parts": sum(
            r.get("elapsed_time", 0) for r in results.values() if r.get("success")
        ),
    }


def compare_performance(query: str) -> dict:
    """比較平行 vs 順序的效能"""

    print(f"\n{'#' * 60}")
    print(f"# 效能比較：{query}")
    print(f"{'#' * 60}")

    # 順序搜尋
    print("\n[1/2] 順序搜尋...")
    seq_result = test_sequential_search(query)

    # 平行搜尋
    print("\n[2/2] 平行搜尋...")
    par_result = test_parallel_search(query)

    # 計算改善
    seq_time = seq_result.get("sum_of_parts", 0)
    par_time = par_result.get("elapsed_time", 0)

    if seq_time > 0:
        improvement = ((seq_time - par_time) / seq_time) * 100
    else:
        improvement = 0

    comparison = {
        "query": query,
        "sequential": {
            "total_time": seq_time,
            "breakdown": {
                name: r.get("elapsed_time", 0)
                for name, r in seq_result.get("results", {}).items()
            },
        },
        "parallel": {
            "total_time": par_time,
            "breakdown": par_result.get("elapsed_breakdown", {}),
        },
        "comparison": {
            "improvement_percent": round(improvement, 1),
            "speedup": round(seq_time / par_time, 2) if par_time > 0 else 0,
        },
    }

    print(f"\n{'=' * 50}")
    print(f"效能比較結果")
    print(f"{'=' * 50}")
    print(f"順序搜尋：{seq_time:.2f}s")
    print(f"平行搜尋：{par_time:.2f}s")
    print(f"效能改善：{improvement:.1f}%")
    print(f"加速比：{seq_time / par_time:.2f}x")

    return comparison


# ===== 主測試流程 =====
def run_tests():
    """執行所有測試"""

    print("\n" + "=" * 60)
    print(" 平行搜尋工具測試 ")
    print("=" * 60)

    all_results = []
    comparisons = []

    for company in TEST_COMPANIES:
        try:
            comparison = compare_performance(company)
            comparisons.append(comparison)
        except Exception as e:
            print(f"\n❌ 測試失敗: {e}")
            all_results.append(
                {
                    "query": company,
                    "error": str(e),
                }
            )

    # 總結
    print("\n" + "=" * 60)
    print(" 測試總結 ")
    print("=" * 60)

    if comparisons:
        avg_improvement = sum(
            c["comparison"]["improvement_percent"] for c in comparisons
        ) / len(comparisons)

        print(f"\n測試公司數：{len(comparisons)}")
        print(f"平均效能改善：{avg_improvement:.1f}%")
        print(f"\n各公司結果：")

        for c in comparisons:
            print(
                f"  - {c['query']}: {c['comparison']['improvement_percent']:.1f}% 改善"
            )

    # 儲存結果
    results_dir = os.path.dirname(os.path.abspath(__file__))
    results_file = os.path.join(results_dir, "test_results.json")

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "comparisons": comparisons,
                "summary": {
                    "avg_improvement": avg_improvement if comparisons else 0,
                    "test_count": len(comparisons),
                },
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n結果已儲存：{results_file}")

    return comparisons


if __name__ == "__main__":
    run_tests()
