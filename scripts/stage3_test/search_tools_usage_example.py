"""
搜尋工具層使用範例
====================

展示如何透過統一的工具層進行搜尋操作
"""

import os
import sys
from search_tools import (
    create_search_tool,
    search_with_tool,
    SearchToolType,
    SearchToolFactory,
)

# ===== 基本使用方式 =====

# 方式一：一步完成搜尋（最簡單）
result = search_with_tool(
    query="澳霸有限公司",
    tool_type="gemini_fewshot",  # 可選: "tavily", "gemini_fewshot", "gemini_planner_tavily"
)
print(f"耗時: {result.elapsed_time:.2f}s")
print(f"資料: {result.data}")


# 方式二：先創建工具再搜尋（可複用）
tool = create_search_tool("tavily", max_results=3)
result1 = tool.search("公司A")
result2 = tool.search("公司B")


# 方式三：使用工廠創建（最彈性）
tool = SearchToolFactory.create(
    SearchToolType.GEMINI_FEWSHOT, model="gemini-2.0-flash", temperature=0.2
)
result = tool.search("澳霸有限公司")


# ===== 主流程整合範例 =====


def main_flow_search(company_name: str, strategy: str = "gemini_fewshot"):
    """
    主流程中的統一搜尋調用

    Args:
        company_name: 公司名稱
        strategy: 搜尋策略 ("tavily", "gemini_fewshot", "gemini_planner_tavily")

    Returns:
        dict: 結構化公司資料
    """
    # 統一的搜尋調用
    result = search_with_tool(query=company_name, tool_type=strategy)

    if result.success:
        return {
            "success": True,
            "data": result.data,
            "elapsed_time": result.elapsed_time,
            "api_calls": result.api_calls,
        }
    else:
        return {
            "success": False,
            "error": "搜尋失敗",
        }


# ===== 在 Lambda 或 API 中使用 =====


def lambda_handler(event, context):
    """
    AWS Lambda 處理常式範例
    """
    company_name = event.get("company_name", "")
    strategy = event.get("strategy", "gemini_fewshot")

    result = search_with_tool(query=company_name, tool_type=strategy)

    return {
        "statusCode": 200,
        "body": result.to_dict(),
    }


# ===== 批量搜尋範例 =====


def batch_search(companies: list, strategy: str = "tavily"):
    """
    批量搜尋多個公司

    Args:
        companies: 公司名稱列表
        strategy: 搜尋策略

    Returns:
        list: 搜尋結果列表
    """
    results = []
    tool = create_search_tool(strategy)  # 創建一次，重複使用

    for company in companies:
        result = tool.search(company)
        results.append(
            {
                "company": company,
                "success": result.success,
                "data": result.data if result.success else None,
                "elapsed_time": result.elapsed_time,
            }
        )

    return results


if __name__ == "__main__":
    # 測試基本功能
    print("=" * 60)
    print("搜尋工具層使用範例")
    print("=" * 60)

    # 基本測試
    result = search_with_tool("澳霸有限公司", "tavily")
    print(f"\nTavily 結果:")
    print(f"  成功: {result.success}")
    print(f"  耗時: {result.elapsed_time:.2f}s")
    print(f"  回答: {result.raw_answer[:100]}...")

    # Gemini Few-shot 測試
    result = search_with_tool("澳霸有限公司", "gemini_fewshot")
    print(f"\nGemini Few-shot 結果:")
    print(f"  成功: {result.success}")
    print(f"  耗時: {result.elapsed_time:.2f}s")
    print(f"  資料: {result.data}")
