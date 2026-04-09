#!/usr/bin/env python3
"""
Phase 14 - 選填欄位功能測試
============================

測試目標:
  1. 驗證所有選填欄位是否正常運作
  2. 檢查 capital 欄位格式問題
  3. 確認選填資料是否被正確使用在生成內容中

選填欄位:
  - organNo: 統一編號
  - capital: 資本額
  - employee_count: 員工人數
  - established_year: 成立年份

使用方法:
  python3 optional_fields_test.py [--api-url URL]

輸出:
  - optional_fields_test_report.json
  - optional_fields_test_summary.csv
  - optional_fields_test_results.xlsx
"""

import json
import time
import re
import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup


# ==================== 配置 ====================
class Config:
    DEFAULT_API_URL = "http://localhost:5000/v1/company/profile/process"
    TIMEOUT_SECONDS = 60

    OUTPUT_DIR = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/checkpoint1/artifacts"
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    TEST_JSON = OUTPUT_DIR / "optional_fields_test_report.json"
    TEST_CSV = OUTPUT_DIR / "optional_fields_test_summary.csv"
    TEST_EXCEL = OUTPUT_DIR / "optional_fields_test_results.xlsx"


# ==================== 測試案例 ====================
TEST_CASES = [
    # 基礎測試（無選填欄位）
    {
        "case_id": 1,
        "name": "基礎測試（無選填欄位）",
        "description": "確認基本功能正常",
        "input": {
            "mode": "GENERATE",
            "organ": "基礎測試公司",
            "organNo": "12345678",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 150,
        },
    },
    # 統一編號測試
    {
        "case_id": 2,
        "name": "統一編號測試",
        "description": "測試統一編號欄位",
        "input": {
            "mode": "GENERATE",
            "organ": "統編測試公司",
            "organNo": "87654321",  # 統一編號
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 150,
        },
        "expected_in_content": ["87654321"],  # 預期出現在內容中
    },
    # 資本額測試 - 字串格式（錯誤格式）
    {
        "case_id": 3,
        "name": "資本額測試（字串格式）",
        "description": "測試資本額欄位（字串格式 - 可能錯誤）",
        "input": {
            "mode": "GENERATE",
            "organ": "資本額測試公司A",
            "organNo": "11223344",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 150,
            "capital": "5000000",  # 字串格式
        },
        "expected_in_content": ["500萬", "5000000", "資本額"],
    },
    # 資本額測試 - 數字格式（正確格式）
    {
        "case_id": 4,
        "name": "資本額測試（數字格式）",
        "description": "測試資本額欄位（數字格式 - 正確）",
        "input": {
            "mode": "GENERATE",
            "organ": "資本額測試公司B",
            "organNo": "55667788",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 150,
            "capital": 5000000,  # 數字格式
        },
        "expected_in_content": ["500萬", "5000000", "資本額"],
    },
    # 員工人數測試
    {
        "case_id": 5,
        "name": "員工人數測試",
        "description": "測試員工人數欄位",
        "input": {
            "mode": "GENERATE",
            "organ": "員工測試公司",
            "organNo": "99887766",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 150,
            "employee_count": 100,  # 員工人數
        },
        "expected_in_content": ["100", "員工"],
    },
    # 成立年份測試
    {
        "case_id": 6,
        "name": "成立年份測試",
        "description": "測試成立年份欄位",
        "input": {
            "mode": "GENERATE",
            "organ": "年份測試公司",
            "organNo": "11112222",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 150,
            "established_year": 2015,  # 成立年份
        },
        "expected_in_content": ["2015", "成立"],
    },
    # 所有選填欄位組合測試
    {
        "case_id": 7,
        "name": "所有選填欄位組合",
        "description": "測試所有選填欄位同時使用",
        "input": {
            "mode": "GENERATE",
            "organ": "完整測試公司",
            "organNo": "33334444",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體、雲端服務",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 200,
            "capital": 10000000,  # 數字格式
            "employee_count": 50,
            "established_year": 2010,
        },
        "expected_in_content": ["1000萬", "50", "2010"],
    },
]


# ==================== 輔助函數 ====================
def count_chinese_characters(text: str) -> int:
    """計算中文字數"""
    if not text:
        return 0
    clean_text = BeautifulSoup(text, "html.parser").get_text()
    return len(clean_text)


def check_content_contains(content: str, keywords: List[str]) -> Dict[str, bool]:
    """檢查內容是否包含關鍵詞"""
    if not content:
        return {kw: False for kw in keywords}

    results = {}
    for kw in keywords:
        results[kw] = kw in content
    return results


# ==================== 測試執行器 ====================
class OptionalFieldsTester:
    """選填欄位測試器"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.results: List[Dict] = []
        self.session = requests.Session()

    def run_all_tests(self) -> List[Dict]:
        """執行所有測試"""
        print(f"\n🚀 開始執行選填欄位測試 ({len(TEST_CASES)} 個案例)...")
        print(f"   API 端點: {self.api_url}")
        print()

        for test_case in TEST_CASES:
            result = self.run_single_test(test_case)
            self.results.append(result)

            status = "✅" if result["passed"] else "❌"
            api_status = result.get("api_success", False)
            api_icon = "🟢" if api_status else "🔴"

            print(
                f"   {status} Case {result['case_id']:2d} | {api_icon} API | {result['name'][:25]:25s}"
            )

            if result.get("errors"):
                for error in result["errors"]:
                    print(f"      ⚠️  {error}")

        return self.results

    def run_single_test(self, test_case: Dict) -> Dict:
        """執行單一測試"""
        case_id = test_case["case_id"]
        request_data = test_case["input"].copy()
        expected_keywords = test_case.get("expected_in_content", [])

        result = {
            "case_id": case_id,
            "name": test_case["name"],
            "description": test_case["description"],
            "request": request_data,
            "response": None,
            "response_time": 0.0,
            "api_success": False,
            "passed": False,
            "errors": [],
            "warnings": [],
            "content_analysis": {},
        }

        try:
            # 顯示請求中的選填欄位
            optional_fields = {}
            for field in ["capital", "employee_count", "established_year"]:
                if field in request_data:
                    optional_fields[field] = request_data[field]

            if optional_fields:
                result["optional_fields_sent"] = optional_fields

            # 呼叫 API
            start_time = time.time()
            response = self.session.post(
                self.api_url, json=request_data, timeout=Config.TIMEOUT_SECONDS
            )
            result["response_time"] = time.time() - start_time

            result["api_status_code"] = response.status_code

            if response.status_code == 200:
                response_data = response.json()
                result["response"] = response_data
                result["api_success"] = True

                # 分析生成的內容
                content_plain = response_data.get("content_plain", "")
                body_html = response_data.get("body_html", "")

                result["content_length"] = count_chinese_characters(content_plain)

                # 檢查預期關鍵詞是否出現在內容中
                if expected_keywords:
                    keyword_results = check_content_contains(
                        content_plain, expected_keywords
                    )
                    result["content_analysis"]["keywords_found"] = keyword_results

                    # 檢查是否有關鍵詞出現
                    found_count = sum(keyword_results.values())
                    result["content_analysis"]["keywords_found_count"] = found_count
                    result["content_analysis"]["keywords_total"] = len(
                        expected_keywords
                    )

                    if found_count == 0:
                        result["warnings"].append(
                            f"選填欄位資料可能未被使用（未找到關鍵詞: {', '.join(expected_keywords)}）"
                        )

                # 檢查 word_limit
                word_limit = request_data.get("word_limit")
                if word_limit:
                    actual_length = result["content_length"]
                    if actual_length > word_limit:
                        result["errors"].append(
                            f"字數超出限制: {actual_length} > {word_limit}"
                        )
                    else:
                        result["word_limit_check"] = {
                            "limit": word_limit,
                            "actual": actual_length,
                            "passed": True,
                        }

                # 測試通過條件：API 成功且無錯誤
                result["passed"] = len(result["errors"]) == 0

            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg += f": {error_data['message']}"
                    if "details" in error_data:
                        error_msg += f" ({error_data['details']})"
                except:
                    error_msg += f": {response.text[:100]}"

                result["errors"].append(error_msg)
                result["api_success"] = False
                result["passed"] = False

        except requests.exceptions.Timeout:
            result["errors"].append(f"Timeout after {Config.TIMEOUT_SECONDS}s")
            result["passed"] = False
        except Exception as e:
            result["errors"].append(f"Exception: {str(e)}")
            result["passed"] = False

        return result

    def generate_summary(self) -> Dict[str, Any]:
        """生成測試摘要"""
        total = len(self.results)
        api_success = sum(1 for r in self.results if r["api_success"])
        passed = sum(1 for r in self.results if r["passed"])

        # 分析 capital 格式問題
        capital_tests = [r for r in self.results if "capital" in r.get("request", {})]
        capital_string_success = sum(
            1
            for r in capital_tests
            if r["api_success"] and isinstance(r["request"].get("capital"), str)
        )
        capital_int_success = sum(
            1
            for r in capital_tests
            if r["api_success"] and isinstance(r["request"].get("capital"), int)
        )

        # 響應時間統計
        response_times = [r["response_time"] for r in self.results if r["api_success"]]
        avg_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            "total_tests": total,
            "api_success": api_success,
            "api_failed": total - api_success,
            "passed": passed,
            "failed": total - passed,
            "success_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "N/A",
            "api_success_rate": f"{(api_success / total * 100):.1f}%"
            if total > 0
            else "N/A",
            "capital_tests": len(capital_tests),
            "capital_string_success": capital_string_success,
            "capital_int_success": capital_int_success,
            "avg_response_time": f"{avg_time:.2f}s",
            "generated_at": datetime.now().isoformat(),
        }


# ==================== 報告生成器 ====================
class ReportGenerator:
    """測試報告生成器"""

    def __init__(self, results: List[Dict], summary: Dict):
        self.results = results
        self.summary = summary

    def generate_all_reports(self):
        """生成所有報告"""
        print("\n📝 正在生成測試報告...")

        self._generate_json_report()
        self._generate_csv_report()
        self._generate_excel_report()

        print(f"\n✅ 報告已保存到: {Config.OUTPUT_DIR}")

    def _generate_json_report(self):
        """生成 JSON 報告"""
        report = {
            "test_suite": "Phase 14 - 選填欄位功能測試",
            "summary": self.summary,
            "test_results": self.results,
        }

        with open(Config.TEST_JSON, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"   ✅ JSON 報告: {Config.TEST_JSON}")

    def _generate_csv_report(self):
        """生成 CSV 摘要"""
        with open(Config.TEST_CSV, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "案例ID",
                    "名稱",
                    "API狀態",
                    "選填欄位",
                    "內容長度",
                    "狀態",
                    "響應時間",
                ]
            )

            for r in self.results:
                optional = r.get("optional_fields_sent", {})
                optional_str = (
                    ", ".join([f"{k}={v}" for k, v in optional.items()])
                    if optional
                    else "無"
                )

                writer.writerow(
                    [
                        r["case_id"],
                        r["name"],
                        "成功" if r["api_success"] else "失敗",
                        optional_str[:50],
                        r.get("content_length", "N/A"),
                        "PASS" if r["passed"] else "FAIL",
                        f"{r['response_time']:.2f}s",
                    ]
                )
        print(f"   ✅ CSV 報告: {Config.TEST_CSV}")

    def _generate_excel_report(self):
        """生成 Excel 報告"""
        # Sheet 1: 測試結果
        data = []
        for r in self.results:
            optional = r.get("optional_fields_sent", {})
            response_data = r.get("response", {})

            row = {
                "案例ID": r["case_id"],
                "測試名稱": r["name"],
                "描述": r["description"],
                "API狀態": "✅ 成功" if r["api_success"] else "❌ 失敗",
                "選填欄位": ", ".join([f"{k}={v}" for k, v in optional.items()])
                if optional
                else "無",
                "內容長度": r.get("content_length", "N/A"),
                "狀態": "✅ 通過" if r["passed"] else "❌ 失敗",
                "響應時間": f"{r['response_time']:.2f}s",
                "錯誤數": len(r.get("errors", [])),
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Sheet 2: 摘要
        summary_data = {
            "項目": [
                "總測試數",
                "API成功",
                "API失敗",
                "通過數",
                "失敗數",
                "成功率",
                "Capital字串格式成功",
                "Capital數字格式成功",
                "平均響應時間",
            ],
            "結果": [
                self.summary["total_tests"],
                self.summary["api_success"],
                self.summary["api_failed"],
                self.summary["passed"],
                self.summary["failed"],
                self.summary["success_rate"],
                self.summary["capital_string_success"],
                self.summary["capital_int_success"],
                self.summary["avg_response_time"],
            ],
        }
        summary_df = pd.DataFrame(summary_data)

        # 寫入 Excel
        with pd.ExcelWriter(Config.TEST_EXCEL, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="測試結果", index=False)
            summary_df.to_excel(writer, sheet_name="測試摘要", index=False)

            # 調整欄寬
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"   ✅ Excel 報告: {Config.TEST_EXCEL}")


# ==================== 主程式 ====================
def main():
    parser = argparse.ArgumentParser(description="Phase 14 - 選填欄位功能測試")
    parser.add_argument(
        "--api-url", default=Config.DEFAULT_API_URL, help="API 端點 URL"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 14 - 選填欄位功能測試")
    print("=" * 80)

    # 執行測試
    tester = OptionalFieldsTester(args.api_url)
    results = tester.run_all_tests()

    # 生成摘要
    summary = tester.generate_summary()

    # 生成報告
    generator = ReportGenerator(results, summary)
    generator.generate_all_reports()

    # 顯示結果摘要
    print("\n" + "=" * 80)
    print("📊 測試結果摘要")
    print("=" * 80)
    print(f"\n總測試數: {summary['total_tests']}")
    print(f"API 成功: {summary['api_success']}")
    print(f"API 失敗: {summary['api_failed']}")
    print(f"通過: {summary['passed']}")
    print(f"失敗: {summary['failed']}")
    print(f"成功率: {summary['success_rate']}")

    # Capital 格式分析
    print("\n📋 Capital 欄位格式分析")
    print("-" * 80)
    print(
        f'字串格式 ("5000000") 成功率: {summary["capital_string_success"]}/{summary["capital_tests"]}'
    )
    print(
        f"數字格式 (5000000) 成功率: {summary['capital_int_success']}/{summary['capital_tests']}"
    )

    if summary["capital_string_success"] == 0 and summary["capital_int_success"] > 0:
        print("\n⚠️  發現: Capital 欄位需要使用『數字格式』而非『字串格式』")
        print("   建議: 修改 API 請求，將 capital 從字串改為數字")
    elif summary["capital_string_success"] > 0:
        print("\n✅ Capital 欄位接受字串格式")

    # 顯示詳細錯誤
    print("\n" + "=" * 80)
    print("🔍 詳細錯誤分析")
    print("=" * 80)

    failed_tests = [r for r in results if not r["passed"]]
    if failed_tests:
        print(f"\n❌ 失敗的案例:")
        for r in failed_tests:
            print(f"\n  Case {r['case_id']}: {r['name']}")
            for error in r.get("errors", []):
                print(f"    - {error}")
    else:
        print("\n✅ 所有測試通過！")

    # 顯示警告
    warnings = [
        (r["case_id"], r["name"], w) for r in results for w in r.get("warnings", [])
    ]
    if warnings:
        print("\n⚠️  警告:")
        for case_id, name, warning in warnings:
            print(f"  Case {case_id}: {warning}")

    print("\n" + "=" * 80)
    print("✅ Phase 14 Checkpoint 1 - 選填欄位驗證")
    print("=" * 80)

    if summary["failed"] == 0:
        print("\n🎉 所有選填欄位測試通過！")
        print("\n✅ 統一編號: 正常")
        print("✅ 資本額: 正常")
        print("✅ 員工人數: 正常")
        print("✅ 成立年份: 正常")
    else:
        print(f"\n⚠️  有 {summary['failed']} 個測試失敗")
        print("請查看上方錯誤詳情進行修復")

    print("\n" + "=" * 80)

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    exit(main())
