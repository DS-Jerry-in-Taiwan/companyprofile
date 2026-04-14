"""
拆分查詢效能測試
================

比較：
1. 現有方式（單一查詢）
2. 拆分查詢（並行多個欄位）
3. 拆分查詢（順序多個欄位）
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

# 測試設定
TEST_COMPANY = "私立揚才文理短期補習班"
ITERATIONS = 3


def test_single_query():
    """測試單一查詢（現有方式）"""
    from src.langgraph_state.company_brief_graph import search_node
    from src.langgraph_state.state import create_initial_state

    times = []

    for i in range(ITERATIONS):
        # 清除單例
        import src.services.config_driven_search as cds

        cds._instance = None
        import importlib
        import src.langgraph_state.company_brief_graph as cbg

        importlib.reload(cds)
        importlib.reload(cbg)

        # 使用 gemini_fewshot
        with open("config/search_config.json", "r") as f:
            config = json.load(f)
        config["search"]["provider"] = "gemini_fewshot"
        with open("config/search_config.json", "w") as f:
            json.dump(config, f, indent=4)

        from src.langgraph_state.company_brief_graph import search_node

        state = create_initial_state(organ=TEST_COMPANY, organ_no="1")

        start = time.time()
        result_state = search_node(state)
        elapsed = time.time() - start
        times.append(elapsed)

        print(f"  [{i + 1}/{ITERATIONS}] {elapsed:.2f}s")

    return times


def test_split_parallel():
    """測試拆分查詢（並行）"""
    sys.path.insert(
        0, os.path.join(PROJECT_ROOT, "scripts", "stage3_test", "split_search")
    )
    from split_search_tool import SplitSearchTool

    times = []

    for i in range(ITERATIONS):
        tool = SplitSearchTool(parallel=True)

        start = time.time()
        result = tool.search(TEST_COMPANY)
        elapsed = time.time() - start
        times.append(elapsed)

        print(f"  [{i + 1}/{ITERATIONS}] {elapsed:.2f}s")

    return times


def test_split_sequential():
    """測試拆分查詢（順序）"""
    sys.path.insert(
        0, os.path.join(PROJECT_ROOT, "scripts", "stage3_test", "split_search")
    )
    from split_search_tool import SplitSearchTool

    times = []

    for i in range(ITERATIONS):
        tool = SplitSearchTool(parallel=False)

        start = time.time()
        result = tool.search(TEST_COMPANY)
        elapsed = time.time() - start
        times.append(elapsed)

        print(f"  [{i + 1}/{ITERATIONS}] {elapsed:.2f}s")

    return times


def main():
    print("=" * 60)
    print("拆分查詢效能測試")
    print("=" * 60)
    print(f"測試公司: {TEST_COMPANY}")
    print(f"測試次數: {ITERATIONS}")
    print()

    # 測試 1: 單一查詢
    print("[1/3] 單一查詢 (gemini_fewshot)")
    single_times = test_single_query()
    print(f"  平均: {statistics.mean(single_times):.2f}s")
    print()

    # 測試 2: 拆分查詢（並行）
    print("[2/3] 拆分查詢（並行）")
    parallel_times = test_split_parallel()
    print(f"  平均: {statistics.mean(parallel_times):.2f}s")
    print()

    # 測試 3: 拆分查詢（順序）
    print("[3/3] 拆分查詢（順序）")
    sequential_times = test_split_sequential()
    print(f"  平均: {statistics.mean(sequential_times):.2f}s")
    print()

    # 結果總結
    print("=" * 60)
    print("結果總結")
    print("=" * 60)

    single_avg = statistics.mean(single_times)
    parallel_avg = statistics.mean(parallel_times)
    sequential_avg = statistics.mean(sequential_times)

    print(f"單一查詢 (gemini_fewshot):    {single_avg:.2f}s")
    print(f"拆分查詢（並行）:             {parallel_avg:.2f}s")
    print(f"拆分查詢（順序）:             {sequential_avg:.2f}s")
    print()

    print("比較:")
    print(
        f"  單一 vs 並行: {single_avg - parallel_avg:.2f}s ({((single_avg - parallel_avg) / single_avg * 100):.1f}%)"
    )
    print(
        f"  單一 vs 順序: {single_avg - sequential_avg:.2f}s ({((single_avg - sequential_avg) / single_avg * 100):.1f}%)"
    )
    print(f"  並行 vs 順序: {parallel_avg - sequential_avg:.2f}s")

    # 標準差
    print()
    print("穩定性（標準差）:")
    print(f"  單一查詢: {statistics.stdev(single_times):.2f}s")
    print(f"  並行拆分: {statistics.stdev(parallel_times):.2f}s")
    print(f"  順序拆分: {statistics.stdev(sequential_times):.2f}s")


if __name__ == "__main__":
    main()
