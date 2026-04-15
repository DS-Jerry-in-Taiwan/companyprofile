#!/usr/bin/env python3
"""
執行平行搜尋速度比較測試

用法：
    python run.py                    # 速度測試（Tavily vs Gemini Flash）
    python run.py --mode full        # 完整流程（搜尋 + 彙整 + 簡介 + 標籤）
    python run.py --mode brief       # 只生成簡介（快速測試）
    python run.py --mode speed        # 速度測試（預設）
    python run.py --company "公司名"  # 指定公司
"""

import os
import sys
import asyncio
import argparse

# 確保路徑正確
_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)

from parallel_runner import ParallelComparisonRunner


def main():
    """執行測試"""
    parser = argparse.ArgumentParser(description="平行搜尋速度比較測試")
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        default="speed",
        choices=["speed", "full", "brief", "compare"],
        help="測試模式：speed(速度測試), full(完整流程), brief(只生成簡介), compare(比較產出)",
    )
    parser.add_argument(
        "--company",
        "-c",
        type=str,
        help="指定測試公司（可指定多個）",
        nargs="+",
    )

    args = parser.parse_args()

    # 模式映射
    mode_map = {
        "speed": "speed_test",
        "full": "full_pipeline",
        "brief": "brief_only",
        "compare": "compare",
    }

    runner = ParallelComparisonRunner()

    # 如果指定了公司，替換測試公司
    if args.company:
        runner.companies = args.company
        print(f"測試公司已設為：{runner.companies}")

    results = asyncio.run(runner.run_all(mode=mode_map[args.mode]))
    runner.save_results(results)

    print("\n" + "=" * 60)
    print("JSON 格式摘要")
    print("=" * 60)
    print(json.dumps(results.get("summary", {}), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import json

    main()
