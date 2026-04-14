#!/usr/bin/env python3
"""
搜尋節點效能測試
================

直接測試搜尋節點，不透過 HTTP
"""

import sys
import os
import time
import json

PROJECT_ROOT = "/home/ubuntu/projects/OrganBriefOptimization"
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# 測試設定
TEST_COMPANY = "私立揚才文理短期補習班"
ITERATIONS = 3


def test_search_node(provider, model=None):
    """測試搜尋節點"""
    import src.services.config_driven_search as cds

    cds._instance = None
    import importlib
    import src.langgraph_state.company_brief_graph as cbg

    importlib.reload(cds)
    importlib.reload(cbg)

    # 修改配置
    config_path = os.path.join(PROJECT_ROOT, "config", "search_config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    config["search"]["provider"] = provider
    if model:
        config["search"]["model"] = model

    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

    # 測試
    from src.langgraph_state.company_brief_graph import search_node
    from src.langgraph_state.state import create_initial_state

    state = create_initial_state(organ=TEST_COMPANY, organ_no="1")

    times = []

    for i in range(ITERATIONS):
        print(f"  測試 {i + 1}/{ITERATIONS}...", end=" ")

        start = time.time()
        result_state = search_node(state)
        elapsed = time.time() - start

        times.append(elapsed)
        print(f"{elapsed:.2f}s")

        if i < ITERATIONS - 1:
            time.sleep(2)

    return times


def main():
    print("=" * 60)
    print("搜尋節點效能測試")
    print("=" * 60)
    print(f"測試公司: {TEST_COMPANY}")
    print(f"測試次數: {ITERATIONS}")
    print()

    # 測試 1: gemini-2.0-flash (預設)
    print("[1/2] gemini-2.0-flash (預設)")
    times_flash = test_search_node("gemini_fewshot", "gemini-2.0-flash")
    avg_flash = sum(times_flash) / len(times_flash)
    print(
        f"  平均: {avg_flash:.2f}s (min: {min(times_flash):.2f}s, max: {max(times_flash):.2f}s)"
    )
    print()

    # 測試 2: gemini-2.0-flash-lite
    print("[2/2] gemini-2.0-flash-lite")
    times_lite = test_search_node("gemini_fewshot", "gemini-2.0-flash-lite")
    avg_lite = sum(times_lite) / len(times_lite)
    print(
        f"  平均: {avg_lite:.2f}s (min: {min(times_lite):.2f}s, max: {max(times_lite):.2f}s)"
    )
    print()

    # 結果
    print("=" * 60)
    print("結果總結")
    print("=" * 60)
    print(f"gemini-2.0-flash:      {avg_flash:.2f}s")
    print(f"gemini-2.0-flash-lite: {avg_lite:.2f}s")

    if avg_lite < avg_flash:
        improvement = ((avg_flash - avg_lite) / avg_flash) * 100
        print(f"\n✅ flash-lite 較快，改善: {improvement:.1f}%")
    else:
        overhead = ((avg_lite - avg_flash) / avg_flash) * 100
        print(f"\n⚠️ flash 較快，額外耗時: {overhead:.1f}%")


if __name__ == "__main__":
    main()
