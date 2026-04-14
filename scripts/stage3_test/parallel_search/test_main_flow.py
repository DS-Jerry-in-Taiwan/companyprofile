#!/usr/bin/env python3
"""
平行搜尋效能測試
================

測試主流程使用平行搜尋的效能
"""

import sys
import os
import time

# 確保使用最新的配置
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

# 測試公司
TEST_COMPANIES = [
    "私立揚才文理短期補習班",
]


def test_parallel_search():
    """測試平行搜尋"""
    print("=" * 60)
    print("平行搜尋效能測試")
    print("=" * 60)

    # 檢查配置
    config_path = os.path.join(PROJECT_ROOT, "config", "search_config.json")
    with open(config_path, "r") as f:
        import json

        config = json.load(f)
        current_provider = config["search"]["provider"]

    print(f"\n當前配置 provider: {current_provider}")
    print()

    # 測試搜尋
    from src.langgraph_state.company_brief_graph import search_node
    from src.langgraph_state.state import create_initial_state

    results = []

    for company in TEST_COMPANIES:
        print(f"測試公司: {company}")
        print("-" * 40)

        # 建立初始狀態
        state = create_initial_state(
            organ=company,
            organ_no="1",
        )

        # 執行搜尋
        start = time.time()
        result_state = search_node(state)
        total_time = time.time() - start

        search_result = result_state.get("search_result")

        print(f"  搜尋來源: {search_result.source}")
        print(f"  搜尋成功: {search_result.success}")
        print(f"  執行時間: {search_result.execution_time:.2f}s")
        print(f"  總耗時: {total_time:.2f}s")
        print()

        results.append(
            {
                "company": company,
                "source": search_result.source,
                "search_time": search_result.execution_time,
                "total_time": total_time,
            }
        )

    # 總結
    print("=" * 60)
    print("測試總結")
    print("=" * 60)

    for r in results:
        print(f"{r['company']}:")
        print(f"  來源: {r['source']}")
        print(f"  搜尋時間: {r['search_time']:.2f}s")

    if results:
        avg_time = sum(r["search_time"] for r in results) / len(results)
        print(f"\n平均搜尋時間: {avg_time:.2f}s")


if __name__ == "__main__":
    # 每次都重新載入模組
    import importlib
    import src.services.config_driven_search
    import src.langgraph_state.company_brief_graph

    # 清除單例
    src.services.config_driven_search._instance = None

    # 重新載入模組
    importlib.reload(src.services.config_driven_search)
    importlib.reload(src.langgraph_state.company_brief_graph)

    test_parallel_search()
