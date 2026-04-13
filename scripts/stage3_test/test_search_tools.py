"""
搜尋工具層完整測試
=====================

測試所有透過 search_tools.py 工具層的搜尋策略
"""

import os
import sys
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from search_tools import (
    SearchToolFactory,
    SearchToolType,
    create_search_tool,
    search_with_tool,
)


def test_all_tools(company_name: str = "澳霸有限公司"):
    """測試所有已註冊的搜尋工具"""

    print("=" * 70)
    print("搜 索 工 具 層 完 整 測 試")
    print("=" * 70)
    print(f"\n測試公司: {company_name}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # ===== 工具一：Tavily 批次 =====
    print(f"\n{'=' * 70}")
    print("工具一：Tavily 批次搜尋")
    print("=" * 70)

    try:
        tool = create_search_tool("tavily")
        result = tool.search(company_name)

        results["tavily_batch"] = result.to_dict()

        print(f"\n✅ 成功")
        print(f"   耗時: {result.elapsed_time:.2f}s")
        print(f"   API 呼叫: {result.api_calls}")
        print(f"   回答長度: {result.answer_length} 字")
        print(f"\n   📋 原始回答:")
        print(f"   {result.raw_answer[:200]}...")

    except Exception as e:
        print(f"❌ 失敗: {e}")
        results["tavily_batch"] = {"success": False, "error": str(e)}

    # ===== 工具二：Gemini Few-shot =====
    print(f"\n{'=' * 70}")
    print("工具二：Gemini Few-shot 搜尋")
    print("=" * 70)

    try:
        tool = create_search_tool("gemini_fewshot")
        result = tool.search(company_name)

        results["gemini_fewshot"] = result.to_dict()

        print(f"\n✅ 成功")
        print(f"   耗時: {result.elapsed_time:.2f}s")
        print(f"   API 呼叫: {result.api_calls}")
        print(f"   回答長度: {result.answer_length} 字")

        print(f"\n   📊 結構化資料:")
        for k, v in result.data.items():
            v_str = str(v)[:50]
            print(f"      {k}: {v_str}...")

    except Exception as e:
        print(f"❌ 失敗: {e}")
        results["gemini_fewshot"] = {"success": False, "error": str(e)}

    # ===== 工具三：Gemini 規劃 + Tavily 執行 =====
    print(f"\n{'=' * 70}")
    print("工具三：Gemini 規劃 + Tavily 執行")
    print("=" * 70)

    try:
        tool = create_search_tool("gemini_planner_tavily")
        result = tool.search(company_name)

        results["gemini_planner_tavily"] = result.to_dict()

        print(f"\n✅ 成功")
        print(f"   耗時: {result.elapsed_time:.2f}s")
        print(f"   API 呼叫: {result.api_calls}")

        print(f"\n   📊 結構化資料:")
        for k, v in result.data.items():
            v_str = str(v)[:50]
            print(f"      {k}: {v_str}...")

    except Exception as e:
        print(f"❌ 失敗: {e}")
        results["gemini_planner_tavily"] = {"success": False, "error": str(e)}

    # ===== 比較總結 =====
    print(f"\n{'=' * 70}")
    print("比 較 總 結")
    print("=" * 70)

    print(f"\n📊 耗時比較:")
    for tool_name, result in results.items():
        if result.get("success"):
            print(
                f"   {tool_name}: {result['elapsed_time']:.2f}s ({result['api_calls']} 次 API)"
            )

    print(f"\n📊 資訊長度:")
    for tool_name, result in results.items():
        if result.get("success"):
            print(f"   {tool_name}: {result['answer_length']} 字")

    print(f"\n📊 格式品質:")
    print(f"   tavily_batch: 自然語言，需要解析 ❌")
    print(f"   gemini_fewshot: JSON 格式，直接可用 ✅")
    print(f"   gemini_planner_tavily: 結構化欄位，直接可用 ✅")

    print(f"\n💡 推薦:")
    print(
        f"   → 速度優先：tavily_batch (快 {results['gemini_fewshot']['elapsed_time'] - results['tavily_batch']['elapsed_time']:.2f}s)"
    )
    print(f"   → 資訊完整：gemini_fewshot (JSON 格式)")

    # 儲存結果
    output_path = os.path.join(
        PROJECT_ROOT, "scripts", "stage3_test", "search_tools_test_results.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "company_name": company_name,
                "timestamp": datetime.now().isoformat(),
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n\n📁 完整結果已儲存至: {output_path}")

    return results


def demo_unified_interface():
    """展示統一的工具調用介面"""

    print("=" * 70)
    print("統 一 工 具 調 用 介 面 演 示")
    print("=" * 70)

    # 方式一：使用工廠直接創建
    print(f"\n方式一：使用工廠直接創建")
    tool = SearchToolFactory.create(SearchToolType.GEMINI_FEWSHOT)
    print(f"   創建工具: {tool.tool_name}")

    # 方式二：使用便捷函式（推薦）
    print(f"\n方式二：使用便捷函式")
    result = search_with_tool(query="澳霸有限公司", tool_type="gemini_fewshot")
    print(f"   搜尋成功: {result.success}")
    print(f"   耗時: {result.elapsed_time:.2f}s")

    # 方式三：帶參數
    print(f"\n方式三：帶參數")
    tool = create_search_tool(tool_type="tavily", max_results=5)
    print(f"   創建工具: {tool.tool_name}")
    print(f"   配置: max_results=5")


if __name__ == "__main__":
    test_all_tools("澳霸有限公司")
    print("\n")
    demo_unified_interface()
