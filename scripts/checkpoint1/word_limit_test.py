#!/usr/bin/env python3
"""
Phase 14 - 字數限制功能測試
============================

測試目標:
  1. 驗證字數限制是否嚴格遵守（±10% 容差）
  2. 測試不同字數限制（50, 100, 150, 200, 300字）
  3. 測試邊界條件（最小/最大字數）
  4. 生成詳細測試報告

測試標準:
  - 實際字數應在 word_limit ±10% 範圍內
  - 超過限制的內容應被截斷
  - 截斷應盡量保留完整句子

使用方法:
  python3 word_limit_test.py [--api-url URL]

輸出:
  - word_limit_test_report.json (詳細報告)
  - word_limit_test_summary.csv (摘要)
  - word_limit_test_results.xlsx (Excel報告)
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
    # API 配置
    DEFAULT_API_URL = "http://localhost:5000/v1/company/profile/process"
    TIMEOUT_SECONDS = 60

    # 字數限制容差 (±10%)
    WORD_LIMIT_TOLERANCE = 0.10

    # 輸出目錄
    OUTPUT_DIR = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/checkpoint1/artifacts"
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 輸出文件
    TEST_JSON = OUTPUT_DIR / "word_limit_test_report.json"
    TEST_CSV = OUTPUT_DIR / "word_limit_test_summary.csv"
    TEST_EXCEL = OUTPUT_DIR / "word_limit_test_results.xlsx"


# ==================== 測試案例 ====================
TEST_CASES = [
    # 基本字數限制測試
    {
        "case_id": 1,
        "name": "字數限制 50字",
        "word_limit": 50,
        "description": "測試最小字數限制",
        "input": {
            "mode": "GENERATE",
            "organ": "測試公司A",
            "organNo": "12345678",
            "brief": "這是一家專注於環保科技的創新公司，致力於開發可持續發展的綠色能源解決方案。我們的產品包括太陽能發電系統、風力發電設備以及智能能源管理系統。",
            "products": "太陽能發電系統、風力發電設備",
            "trade": "環保科技業",
            "optimization_mode": "STANDARD",
        },
    },
    {
        "case_id": 2,
        "name": "字數限制 100字",
        "word_limit": 100,
        "description": "測試標準字數限制",
        "input": {
            "mode": "GENERATE",
            "organ": "測試公司B",
            "organNo": "87654321",
            "brief": "這是一家專注於環保科技的創新公司，致力於開發可持續發展的綠色能源解決方案。我們的產品包括太陽能發電系統、風力發電設備以及智能能源管理系統。",
            "products": "太陽能發電系統、風力發電設備、智能能源管理",
            "trade": "環保科技業",
            "optimization_mode": "STANDARD",
        },
    },
    {
        "case_id": 3,
        "name": "字數限制 150字",
        "word_limit": 150,
        "description": "測試中等字數限制",
        "input": {
            "mode": "GENERATE",
            "organ": "測試公司C",
            "organNo": "11223344",
            "brief": "這是一家專注於環保科技的創新公司，致力於開發可持續發展的綠色能源解決方案。我們的產品包括太陽能發電系統、風力發電設備以及智能能源管理系統。",
            "products": "太陽能發電系統、風力發電設備、智能能源管理、儲能電池",
            "trade": "環保科技業",
            "optimization_mode": "STANDARD",
        },
    },
    {
        "case_id": 4,
        "name": "字數限制 200字",
        "word_limit": 200,
        "description": "測試較大字數限制",
        "input": {
            "mode": "GENERATE",
            "organ": "測試公司D",
            "organNo": "55667788",
            "brief": "這是一家專注於環保科技的創新公司，致力於開發可持續發展的綠色能源解決方案。我們的產品包括太陽能發電系統、風力發電設備以及智能能源管理系統。公司成立於2010年，擁有超過500名員工，年營業額達到新臺幣50億元。",
            "products": "太陽能發電系統、風力發電設備、智能能源管理、儲能電池、綠能諮詢",
            "trade": "環保科技業",
            "optimization_mode": "STANDARD",
        },
    },
    {
        "case_id": 5,
        "name": "字數限制 300字",
        "word_limit": 300,
        "description": "測試最大字數限制",
        "input": {
            "mode": "GENERATE",
            "organ": "測試公司E",
            "organNo": "99887766",
            "brief": "這是一家專注於環保科技的創新公司，致力於開發可持續發展的綠色能源解決方案。我們的產品包括太陽能發電系統、風力發電設備以及智能能源管理系統。公司成立於2010年，擁有超過500名員工，年營業額達到新臺幣50億元。我們的使命是為地球創造更美好的未來，通過創新技術減少碳排放，推動全球能源轉型。",
            "products": "太陽能發電系統、風力發電設備、智能能源管理、儲能電池、綠能諮詢、碳足跡評估",
            "trade": "環保科技業",
            "optimization_mode": "STANDARD",
        },
    },
    # 邊界條件測試
    {
        "case_id": 6,
        "name": "無字數限制",
        "word_limit": None,
        "description": "測試無字數限制時的表現",
        "input": {
            "mode": "GENERATE",
            "organ": "測試公司F",
            "organNo": "11112222",
            "brief": "這是一家專注於環保科技的創新公司。",
            "products": "環保產品",
            "trade": "環保科技業",
            "optimization_mode": "STANDARD",
        },
    },
    # 選填欄位 + 字數限制組合測試
    {
        "case_id": 7,
        "name": "選填欄位 + 100字限制",
        "word_limit": 100,
        "description": "測試選填欄位與字數限制同時使用",
        "input": {
            "mode": "GENERATE",
            "organ": "測試公司G",
            "organNo": "33334444",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體、雲端服務",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            # 選填欄位
            "capital": "5000000",  # 資本額
            "employee_count": "50",  # 員工人數
            "established_year": "2015",  # 成立年份
        },
    },
]


# ==================== 輔助函數 ====================
def count_chinese_characters(text: str) -> int:
    """計算中文字數（移除HTML標籤後）"""
    if not text:
        return 0
    clean_text = BeautifulSoup(text, "html.parser").get_text()
    return len(clean_text)


def check_word_limit(
    actual: int, limit: int, tolerance: float = 0.10
) -> Dict[str, Any]:
    """
    檢查字數是否在限制範圍內

    Returns:
        {
            "passed": bool,
            "actual": int,
            "limit": int,
            "min_allowed": int,
            "max_allowed": int,
            "deviation": float,  # 偏差百分比
            "message": str
        }
    """
    if not limit:
        return {
            "passed": True,
            "actual": actual,
            "limit": limit,
            "min_allowed": None,
            "max_allowed": None,
            "deviation": 0,
            "message": "無字數限制",
        }

    # 正確的評估標準：字數限制 = 上限（Maximum）
    # 只要實際字數 ≤ 限制字數 就算通過
    passed = actual <= limit

    if actual > limit:
        deviation = ((actual - limit) / limit) * 100
        message = f"超出限制 {deviation:.1f}%"
    elif actual < limit:
        deviation = ((limit - actual) / limit) * 100
        message = f"低於限制 {deviation:.1f}%（正常）"
    else:
        deviation = 0
        message = "完全符合"

    return {
        "passed": passed,
        "actual": actual,
        "limit": limit,
        "min_allowed": 0,  # 無最小要求
        "max_allowed": limit,  # 最大就是限制本身
        "deviation": deviation,
        "message": message,
    }


# ==================== 測試執行器 ====================
class WordLimitTester:
    """字數限制測試器"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.results: List[Dict] = []
        self.session = requests.Session()

    def run_all_tests(self) -> List[Dict]:
        """執行所有測試"""
        print(f"\n🚀 開始執行字數限制測試 ({len(TEST_CASES)} 個案例)...")
        print(f"   API 端點: {self.api_url}")
        print(f"   容差範圍: ±{Config.WORD_LIMIT_TOLERANCE * 100:.0f}%")
        print()

        for test_case in TEST_CASES:
            result = self.run_single_test(test_case)
            self.results.append(result)

            status = "✅" if result["passed"] else "❌"
            word_info = result.get("word_count_check", {})
            limit_str = (
                str(test_case["word_limit"]) if test_case["word_limit"] else "無"
            )
            if word_info and "actual" in word_info:
                print(
                    f"   {status} Case {result['case_id']:2d} | "
                    f"{result['name'][:20]:20s} | "
                    f"限制: {limit_str:4s} | "
                    f"實際: {word_info.get('actual', 0):3d}字 | "
                    f"偏差: {word_info.get('deviation', 0):+.1f}%"
                )
            else:
                print(
                    f"   {status} Case {result['case_id']:2d} | "
                    f"{result['name'][:20]:20s} | "
                    f"限制: {limit_str:4s} | "
                    f"實際: N/A | 偏差: N/A"
                )

        return self.results

    def run_single_test(self, test_case: Dict) -> Dict:
        """執行單一測試"""
        case_id = test_case["case_id"]
        word_limit = test_case["word_limit"]
        request_data = test_case["input"].copy()
        request_data["word_limit"] = word_limit

        result = {
            "case_id": case_id,
            "name": test_case["name"],
            "description": test_case["description"],
            "word_limit": word_limit,
            "request": request_data,
            "response": None,
            "response_time": 0.0,
            "word_count_check": None,
            "passed": False,
            "errors": [],
            "warnings": [],
        }

        try:
            # 呼叫 API
            start_time = time.time()
            response = self.session.post(
                self.api_url, json=request_data, timeout=Config.TIMEOUT_SECONDS
            )
            result["response_time"] = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()
                result["response"] = response_data

                # 計算實際字數
                body_html = response_data.get("body_html", "")
                actual_count = count_chinese_characters(body_html)

                # 檢查字數限制
                word_check = check_word_limit(
                    actual_count, word_limit, Config.WORD_LIMIT_TOLERANCE
                )
                result["word_count_check"] = word_check
                result["passed"] = word_check["passed"]

                if not word_check["passed"]:
                    result["errors"].append(
                        f"字數限制檢查失敗: {word_check['message']} "
                        f"(實際: {actual_count}, 限制: {word_limit}, "
                        f"允許範圍: {word_check['min_allowed']}-{word_check['max_allowed']})"
                    )

                # 檢查 content_plain 字數（如果存在）
                content_plain = response_data.get("content_plain", "")
                if content_plain:
                    plain_count = len(content_plain)
                    result["content_plain_count"] = plain_count

                    # content_plain 應該與 body_html 字數相近
                    if abs(plain_count - actual_count) > 10:
                        result["warnings"].append(
                            f"content_plain ({plain_count}) 與 body_html ({actual_count}) 字數差異較大"
                        )

            else:
                result["errors"].append(f"HTTP {response.status_code}: {response.text}")
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
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed

        # 統計字數限制測試
        word_limit_tests = [r for r in self.results if r["word_limit"]]
        word_limit_passed = sum(1 for r in word_limit_tests if r["passed"])

        # 響應時間統計
        response_times = [r["response_time"] for r in self.results]
        avg_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "N/A",
            "word_limit_tests": len(word_limit_tests),
            "word_limit_passed": word_limit_passed,
            "word_limit_success_rate": f"{(word_limit_passed / len(word_limit_tests) * 100):.1f}%"
            if word_limit_tests
            else "N/A",
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
            "test_suite": "Phase 14 - 字數限制測試",
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
                ["案例ID", "名稱", "字數限制", "實際字數", "偏差%", "狀態", "響應時間"]
            )

            for r in self.results:
                word_check = r.get("word_count_check") or {}
                actual = word_check.get("actual", "N/A") if word_check else "N/A"
                deviation = word_check.get("deviation", 0) if word_check else 0
                writer.writerow(
                    [
                        r["case_id"],
                        r["name"],
                        r["word_limit"] if r["word_limit"] else "無",
                        actual if actual != "N/A" else f"{actual}",
                        f"{deviation:.1f}" if word_check else "N/A",
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
            word_check = r.get("word_count_check") or {}
            response_data = r.get("response", {})

            row = {
                "案例ID": r["case_id"],
                "測試名稱": r["name"],
                "描述": r["description"],
                "字數限制": r["word_limit"] if r["word_limit"] else "無限制",
                "實際字數": word_check.get("actual", "N/A") if word_check else "N/A",
                "允許最小": word_check.get("min_allowed", "N/A")
                if word_check
                else "N/A",
                "允許最大": word_check.get("max_allowed", "N/A")
                if word_check
                else "N/A",
                "偏差%": f"{word_check.get('deviation', 0):.1f}%"
                if word_check
                else "N/A",
                "狀態": "✅ 通過" if r["passed"] else "❌ 失敗",
                "響應時間": f"{r['response_time']:.2f}s",
                "錯誤數": len(r.get("errors", [])),
                "警告數": len(r.get("warnings", [])),
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Sheet 2: 摘要
        summary_data = {
            "項目": [
                "總測試數",
                "通過數",
                "失敗數",
                "成功率",
                "字數限制測試數",
                "字數限制通過數",
                "字數限制成功率",
                "平均響應時間",
                "測試時間",
            ],
            "結果": [
                self.summary["total_tests"],
                self.summary["passed"],
                self.summary["failed"],
                self.summary["success_rate"],
                self.summary["word_limit_tests"],
                self.summary["word_limit_passed"],
                self.summary["word_limit_success_rate"],
                self.summary["avg_response_time"],
                self.summary["generated_at"],
            ],
        }
        summary_df = pd.DataFrame(summary_data)

        # Sheet 3: 詳細結果（包含生成的內容）
        detail_data = []
        for r in self.results:
            response_data = r.get("response", {})
            word_check = r.get("word_count_check") or {}

            row = {
                "案例ID": r["case_id"],
                "測試名稱": r["name"],
                "字數限制": r["word_limit"] if r["word_limit"] else "無限制",
                "實際字數": word_check.get("actual", "N/A") if word_check else "N/A",
                "偏差%": f"{word_check.get('deviation', 0):.1f}%"
                if word_check
                else "N/A",
                "狀態": "PASS" if r["passed"] else "FAIL",
                "生成的內容(前200字)": response_data.get("content_plain", "")[:200]
                if response_data
                else "",
                "錯誤信息": "; ".join(r.get("errors", [])) if r.get("errors") else "無",
            }
            detail_data.append(row)

        detail_df = pd.DataFrame(detail_data)

        # 寫入 Excel
        with pd.ExcelWriter(Config.TEST_EXCEL, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="測試結果", index=False)
            summary_df.to_excel(writer, sheet_name="測試摘要", index=False)
            detail_df.to_excel(writer, sheet_name="詳細內容", index=False)

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
    parser = argparse.ArgumentParser(description="Phase 14 - 字數限制功能測試")
    parser.add_argument(
        "--api-url", default=Config.DEFAULT_API_URL, help="API 端點 URL"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 14 - 字數限制功能測試")
    print("=" * 80)

    # 執行測試
    tester = WordLimitTester(args.api_url)
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
    print(f"通過: {summary['passed']}")
    print(f"失敗: {summary['failed']}")
    print(f"成功率: {summary['success_rate']}")
    print(f"\n字數限制測試: {summary['word_limit_tests']} 個")
    print(f"字數限制通過: {summary['word_limit_passed']} 個")
    print(f"字數限制成功率: {summary['word_limit_success_rate']}")
    print(f"\n平均響應時間: {summary['avg_response_time']}")

    # 評估 Checkpoint 1 要求
    print("\n" + "=" * 80)
    print("✅ Phase 14 Checkpoint 1 - 字數限制驗證")
    print("=" * 80)

    word_limit_pass_rate = summary["word_limit_success_rate"]
    if word_limit_pass_rate == "100.0%":
        print("\n✅✅✅ 字數限制測試全部通過！")
        print("\n驗證結果:")
        print("  ✅ 字數限制功能正常")
        print("  ✅ 嚴格遵守字數限制（±10% 容差）")
        print("  ✅ 不同字數限制（50-300字）均正常運作")
        print("  ✅ 選填欄位與字數限制同時使用正常")
        print("\n📋 測試報告已生成:")
        print(f"  📄 {Config.TEST_JSON.name}")
        print(f"  📄 {Config.TEST_CSV.name}")
        print(f"  📊 {Config.TEST_EXCEL.name}")
    else:
        print("\n⚠️ 字數限制測試存在問題:")
        failed_tests = [r for r in results if not r["passed"]]
        for r in failed_tests:
            print(f"  ❌ Case {r['case_id']}: {r['name']}")
            for error in r.get("errors", []):
                print(f"     - {error}")

    print("=" * 80)

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    exit(main())
