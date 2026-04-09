#!/usr/bin/env python3
"""
Phase 14 Checkpoint 1 - 自動化測試腳本
========================================
使用 test_inputs_api.json 進行自動化 API 測試

測試項目:
1. Bug B - 字數限制功能
2. Bug C - 冗餘短語移除
3. Bug D - 回應時間 (<5秒)

使用方法:
  python3 automated_checkpoint1_test.py [--api-url URL]

輸出:
  - checkpoint1_test_report.json  (詳細測試結果)
  - checkpoint1_test_report.md    (可讀報告)
  - checkpoint1_summary.csv       (摘要表格)
"""

import json
import re
import time
import csv
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests


# ==================== 配置 ====================
class Config:
    # 輸入文件
    INPUT_JSON = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/test_inputs_api.json"
    )
    OUTPUT_DIR = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1"
    )

    # 輸出文件
    OUTPUT_JSON = OUTPUT_DIR / "checkpoint1_test_report.json"
    OUTPUT_MD = OUTPUT_DIR / "checkpoint1_test_report.md"
    OUTPUT_CSV = OUTPUT_DIR / "checkpoint1_summary.csv"

    # API 配置
    DEFAULT_API_URL = "http://localhost:5000/v1/company/profile/process"

    # 測試配置
    TIMEOUT_SECONDS = 30
    MAX_RESPONSE_TIME = 5.0  # Bug D 目標
    WORD_LIMIT_TOLERANCE = 10  # 字數限制容差

    # Bug C - 冗餘短語模式
    VERBOSE_PATTERNS = [
        r"以下是.*?優化",
        r"以下是.*?描述",
        r"以下是.*?結果",
        r"以下是.*?版本",
        r"Below is.*?optimized",
        r"優化後的.*?版本",
        r"以下是為您",
    ]


# ==================== 測試結果模型 ====================
class TestResult:
    """單一測試結果"""

    def __init__(self, case_id: int):
        self.case_id = case_id
        self.request_data: Dict = {}
        self.response_data: Dict = {}
        self.response_time: float = 0.0
        self.success: bool = False
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.validation_results: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "request": self.request_data,
            "response": self.response_data,
            "response_time": f"{self.response_time:.2f}s",
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "validation": self.validation_results,
        }


# ==================== API 測試器 ====================
class APITester:
    """API 自動化測試器"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.results: List[TestResult] = []
        self.session = requests.Session()

    def load_test_cases(self) -> List[Dict]:
        """載入測試案例"""
        try:
            with open(Config.INPUT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("test_cases", [])
        except Exception as e:
            print(f"❌ 無法載入測試案例: {e}")
            return []

    def run_all_tests(self, test_cases: List[Dict]) -> List[TestResult]:
        """執行所有測試"""
        print(f"\n🚀 開始執行 {len(test_cases)} 個測試案例...")
        print(f"   API 端點: {self.api_url}")
        print()

        for i, test_case in enumerate(test_cases, 1):
            result = self.run_single_test(test_case)
            self.results.append(result)

            # 顯示進度
            status = "✅" if result.success else "❌"
            print(
                f"   {status} Case {result.case_id:2d} | "
                f"Time: {result.response_time:.2f}s | "
                f"Errors: {len(result.errors)}"
            )

        return self.results

    def run_single_test(self, test_case: Dict) -> TestResult:
        """執行單一測試"""
        case_id = test_case["case_id"]
        request_data = test_case["request"]

        result = TestResult(case_id)
        result.request_data = request_data

        try:
            # 發送 API 請求
            start_time = time.time()
            response = self.session.post(
                self.api_url, json=request_data, timeout=Config.TIMEOUT_SECONDS
            )
            result.response_time = time.time() - start_time

            # 檢查回應狀態
            if response.status_code == 200:
                result.response_data = response.json()
                result.success = True

                # 執行驗證
                self._validate_response(result)
            else:
                result.errors.append(f"HTTP {response.status_code}: {response.text}")
                result.success = False

        except requests.exceptions.Timeout:
            result.errors.append(f"Timeout after {Config.TIMEOUT_SECONDS}s")
            result.success = False
        except Exception as e:
            result.errors.append(f"Exception: {str(e)}")
            result.success = False

        return result

    def _validate_response(self, result: TestResult):
        """驗證回應內容"""
        # API 回應使用 body_html 而不是 result
        output_text = result.response_data.get("body_html", "")

        # 驗證 1: 回應時間 (Bug D)
        time_check = result.response_time <= Config.MAX_RESPONSE_TIME
        result.validation_results["response_time_check"] = {
            "passed": time_check,
            "actual": f"{result.response_time:.2f}s",
            "threshold": f"{Config.MAX_RESPONSE_TIME}s",
        }

        if not time_check:
            result.warnings.append(
                f"Response time {result.response_time:.2f}s exceeds {Config.MAX_RESPONSE_TIME}s"
            )

        # 驗證 2: 冗餘短語 (Bug C)
        verbose_found = []
        for pattern in Config.VERBOSE_PATTERNS:
            if re.search(pattern, output_text[:200]):  # 檢查前200字
                verbose_found.append(pattern)

        verbose_check = len(verbose_found) == 0
        result.validation_results["verbose_phrase_check"] = {
            "passed": verbose_check,
            "patterns_found": verbose_found,
        }

        if not verbose_check:
            result.errors.append(f"Found verbose phrases: {verbose_found}")

        # 驗證 3: 字數統計
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", output_text))
        result.validation_results["word_count"] = {
            "chinese_chars": chinese_chars,
            "total_chars": len(output_text),
        }

    def generate_summary(self) -> Dict[str, Any]:
        """生成測試摘要"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful

        # 計算平均回應時間
        avg_time = (
            sum(r.response_time for r in self.results) / total if total > 0 else 0
        )

        # Bug C 統計
        verbose_issues = sum(
            1
            for r in self.results
            if not r.validation_results.get("verbose_phrase_check", {}).get(
                "passed", True
            )
        )

        # Bug D 統計
        slow_responses = sum(
            1
            for r in self.results
            if not r.validation_results.get("response_time_check", {}).get(
                "passed", True
            )
        )

        return {
            "total_tests": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful / total * 100):.1f}%"
            if total > 0
            else "N/A",
            "avg_response_time": f"{avg_time:.2f}s",
            "bug_c_verbose_phrases": verbose_issues,
            "bug_d_slow_responses": slow_responses,
            "generated_at": datetime.now().isoformat(),
        }


# ==================== 報告生成器 ====================
def generate_reports(results: List[TestResult], summary: Dict[str, Any]):
    """生成測試報告"""

    # 1. JSON 詳細報告
    report = {
        "test_suite": "Phase 14 Checkpoint 1",
        "summary": summary,
        "test_results": [r.to_dict() for r in results],
    }

    with open(Config.OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON 報告: {Config.OUTPUT_JSON}")

    # 2. CSV 摘要
    with open(Config.OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["案例ID", "狀態", "回應時間", "字數", "冗餘短語", "錯誤數"])

        for r in results:
            word_count = r.validation_results.get("word_count", {}).get(
                "chinese_chars", 0
            )
            verbose_count = len(
                r.validation_results.get("verbose_phrase_check", {}).get(
                    "patterns_found", []
                )
            )
            status = "PASS" if r.success and len(r.errors) == 0 else "FAIL"

            writer.writerow(
                [
                    r.case_id,
                    status,
                    f"{r.response_time:.2f}s",
                    word_count,
                    verbose_count,
                    len(r.errors),
                ]
            )
    print(f"✅ CSV 報告: {Config.OUTPUT_CSV}")

    # 3. Markdown 報告
    md = f"""# Phase 14 Checkpoint 1 - 自動化測試報告

## 📊 測試摘要

| 指標 | 數值 |
|------|------|
| 總測試數 | {summary["total_tests"]} |
| 成功 | {summary["successful"]} |
| 失敗 | {summary["failed"]} |
| 成功率 | {summary["success_rate"]} |
| 平均回應時間 | {summary["avg_response_time"]} |

## 🐛 Bug 驗證結果

| Bug | 描述 | 狀態 | 問題數 |
|-----|------|------|--------|
| B | 字數限制 | 待驗證 | - |
| C | 冗餘短語 | {"✅ 通過" if summary["bug_c_verbose_phrases"] == 0 else "❌ 失敗"} | {summary["bug_c_verbose_phrases"]} |
| D | 回應時間 | {"✅ 通過" if summary["bug_d_slow_responses"] == 0 else "❌ 失敗"} | {summary["bug_d_slow_responses"]} |

## 📋 詳細測試結果

| ID | 狀態 | 時間 | 字數 | 冗餘 | 錯誤 |
|----|------|------|------|------|------|
"""

    for r in results:
        word_count = r.validation_results.get("word_count", {}).get("chinese_chars", 0)
        verbose_count = len(
            r.validation_results.get("verbose_phrase_check", {}).get(
                "patterns_found", []
            )
        )
        status_icon = "✅" if r.success and len(r.errors) == 0 else "❌"

        md += f"| {r.case_id} | {status_icon} | {r.response_time:.2f}s | {word_count} | {verbose_count} | {len(r.errors)} |\n"

    # 添加失敗案例詳情
    failed_results = [r for r in results if not r.success or len(r.errors) > 0]
    if failed_results:
        md += """
## ❌ 失敗案例詳情

"""
        for r in failed_results:
            md += f"""### Case {r.case_id}

- **狀態**: {"API 錯誤" if not r.success else "驗證失敗"}
- **回應時間**: {r.response_time:.2f}s
- **錯誤**:
"""
            for error in r.errors:
                md += f"  - {error}\n"

            if r.warnings:
                md += "- **警告**:\n"
                for warning in r.warnings:
                    md += f"  - {warning}\n"

            md += "\n"

    md += f"""
---

*Report generated at: {summary["generated_at"]}*
"""

    with open(Config.OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ Markdown 報告: {Config.OUTPUT_MD}")


# ==================== 主程式 ====================
def main():
    parser = argparse.ArgumentParser(description="Phase 14 Checkpoint 1 自動化測試")
    parser.add_argument(
        "--api-url",
        default=Config.DEFAULT_API_URL,
        help=f"API 端點 URL (預設: {Config.DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="只載入測試案例，不執行 API 調用"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Phase 14 Checkpoint 1 - 自動化測試")
    print("=" * 70)

    # 初始化測試器
    tester = APITester(args.api_url)

    # 載入測試案例
    test_cases = tester.load_test_cases()
    if not test_cases:
        print("❌ 無法載入測試案例")
        return 1

    print(f"✅ 載入 {len(test_cases)} 個測試案例")

    if args.dry_run:
        print("\n📋 乾跑模式 - 測試案例預覽:")
        for tc in test_cases:
            print(f"   Case {tc['case_id']}: {tc['request']['company_name']}")
        return 0

    # 執行測試
    results = tester.run_all_tests(test_cases)

    # 生成摘要
    summary = tester.generate_summary()

    # 生成報告
    print("\n📝 正在生成報告...")
    generate_reports(results, summary)

    # 顯示結果
    print("\n" + "=" * 70)
    print("📊 測試結果摘要")
    print("=" * 70)
    print(f"\n總測試數: {summary['total_tests']}")
    print(f"成功: {summary['successful']}")
    print(f"失敗: {summary['failed']}")
    print(f"成功率: {summary['success_rate']}")
    print(f"\n平均回應時間: {summary['avg_response_time']}")
    print(f"Bug C (冗餘短語) 問題: {summary['bug_c_verbose_phrases']}")
    print(f"Bug D (回應時間) 問題: {summary['bug_d_slow_responses']}")

    # Checkpoint 1 狀態
    print("\n" + "=" * 70)
    print("🎯 Checkpoint 1 狀態")
    print("=" * 70)

    checkpoint_pass = (
        summary["bug_c_verbose_phrases"] == 0 and summary["success_rate"] == "100.0%"
    )

    if checkpoint_pass:
        print("\n✅ Checkpoint 1 PASSED")
        print("   - Bug C (冗餘短語): 已修復")
        print("   - 所有測試通過")
        print("\n🚀 可以進入 Stage 2 (效能優化)")
    else:
        print("\n❌ Checkpoint 1 FAILED")
        if summary["bug_c_verbose_phrases"] > 0:
            print(f"   - Bug C (冗餘短語): {summary['bug_c_verbose_phrases']} 個問題")
        if summary["failed"] > 0:
            print(f"   - API 錯誤: {summary['failed']} 個失敗")
        print("\n⚠️  需要修復問題後再進行 Checkpoint 1")

    print(f"\n✅ 報告已保存到: {Config.OUTPUT_DIR}")

    return 0 if checkpoint_pass else 1


if __name__ == "__main__":
    exit(main())
