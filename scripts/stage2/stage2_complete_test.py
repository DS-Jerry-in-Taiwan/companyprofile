#!/usr/bin/env python3
"""
Phase 14 Stage 2 - 完整測試腳本
================================

測試項目:
  1. 輸入資訊使用率 (檢查 capital, employee_count, established_year 是否被使用)
  2. 中國用語檢測
  3. 格式一致性檢查 (Bug B)
  4. 性能基準測試 (與 Checkpoint 1 對比)

使用方法:
  python3 stage2_complete_test.py [--api-url URL]

輸出:
  - stage2_test_report.json
  - stage2_test_summary.csv
  - stage2_test_results.xlsx
"""

import json
import time
import re
import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

# 引入中國用語檢測器
sys.path.insert(0, str(Path(__file__).parent))
from china_term_checker import ChinaTermChecker


# ==================== 配置 ====================
class Config:
    DEFAULT_API_URL = "http://localhost:5000/v1/company/profile/process"
    TIMEOUT_SECONDS = 60

    OUTPUT_DIR = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/stage2/artifacts"
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    TEST_JSON = OUTPUT_DIR / "stage2_test_report.json"
    TEST_CSV = OUTPUT_DIR / "stage2_test_summary.csv"
    TEST_EXCEL = OUTPUT_DIR / "stage2_test_results.xlsx"

    # Stage 2 目標
    TARGET_RESPONSE_TIME = 2.0  # 目標響應時間 <2秒
    TARGET_INFO_USAGE_RATE = 0.8  # 目標資訊使用率 80%


# ==================== 測試案例 ====================
TEST_CASES = [
    # 測試 1: 基礎案例（檢查無選填欄位時的表現）
    {
        "case_id": 1,
        "name": "基礎案例（無選填欄位）",
        "description": "確認基本功能正常運作",
        "input": {
            "mode": "GENERATE",
            "organ": "基礎測試公司",
            "organNo": "12345678",
            "brief": "這是一家專注於環保科技的創新公司，致力於開發可持續發展的綠色能源解決方案。",
            "products": "太陽能發電系統、風力發電設備",
            "trade": "環保科技業",
            "optimization_mode": "STANDARD",
            "word_limit": 200,
        },
        "checks": ["response_time", "format", "china_terms"],
    },
    # 測試 2: 資本額使用情況
    {
        "case_id": 2,
        "name": "資本額使用測試",
        "description": "檢查 capital 資訊是否被使用",
        "input": {
            "mode": "GENERATE",
            "organ": "資本額測試公司",
            "organNo": "87654321",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 200,
            "capital": 10000000,  # 1000萬
        },
        "checks": ["response_time", "format", "china_terms", "info_usage"],
        "expected_keywords": ["1000萬", "資本", "資本額", "10000000"],
    },
    # 測試 3: 員工人數使用情況
    {
        "case_id": 3,
        "name": "員工人數使用測試",
        "description": "檢查 employee_count 資訊是否被使用",
        "input": {
            "mode": "GENERATE",
            "organ": "員工測試公司",
            "organNo": "11223344",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 200,
            "employee_count": 500,
        },
        "checks": ["response_time", "format", "china_terms", "info_usage"],
        "expected_keywords": ["500", "員工", "人"],
    },
    # 測試 4: 成立年份使用情況
    {
        "case_id": 4,
        "name": "成立年份使用測試",
        "description": "檢查 established_year 資訊是否被使用",
        "input": {
            "mode": "GENERATE",
            "organ": "年份測試公司",
            "organNo": "55667788",
            "brief": "這是一家專注於軟體開發的科技公司。",
            "products": "企業軟體",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 200,
            "established_year": 2010,
        },
        "checks": ["response_time", "format", "china_terms", "info_usage"],
        "expected_keywords": ["2010", "成立", "年"],
    },
    # 測試 5: 全部選填欄位
    {
        "case_id": 5,
        "name": "全部選填欄位測試",
        "description": "檢查所有選填欄位資訊使用率",
        "input": {
            "mode": "GENERATE",
            "organ": "完整測試公司",
            "organNo": "99887766",
            "brief": "這是一家專注於軟體開發的科技公司，致力於提供優質的企業解決方案。",
            "products": "企業軟體、雲端服務、AI解決方案",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 250,
            "capital": 50000000,  # 5000萬
            "employee_count": 200,
            "established_year": 2005,
        },
        "checks": ["response_time", "format", "china_terms", "info_usage"],
        "expected_keywords": ["5000萬", "200", "2005", "資本", "員工", "成立"],
    },
    # 測試 6: 中國用語檢測案例
    {
        "case_id": 6,
        "name": "中國用語檢測案例",
        "description": "檢查生成內容是否出現中國用語",
        "input": {
            "mode": "GENERATE",
            "organ": "用語檢測公司",
            "organNo": "11112222",
            "brief": "我們公司提供優質的軟件開發服務，服務器運行穩定，為用戶提供信息服務。",
            "products": "軟體開發、系統整合",
            "trade": "資訊軟體業",
            "optimization_mode": "STANDARD",
            "word_limit": 200,
        },
        "checks": ["response_time", "format", "china_terms"],
    },
    # 測試 7: 格式一致性測試
    {
        "case_id": 7,
        "name": "格式一致性測試",
        "description": "檢查標點符號和換行格式",
        "input": {
            "mode": "GENERATE",
            "organ": "格式測試公司",
            "organNo": "33334444",
            "brief": "測試公司專注於提供高品質產品。我們的服務優秀。客戶滿意度高。",
            "products": "企業服務",
            "trade": "商業服務業",
            "optimization_mode": "STANDARD",
            "word_limit": 200,
        },
        "checks": ["response_time", "format", "china_terms", "punctuation"],
    },
    # 測試 8: 性能壓力測試（較大字數）
    {
        "case_id": 8,
        "name": "性能壓力測試（300字）",
        "description": "測試較大字數限制的響應時間",
        "input": {
            "mode": "GENERATE",
            "organ": "性能測試公司",
            "organNo": "55556666",
            "brief": "這是一家規模龐大的企業，在多個領域都有業務。我們提供多樣化的產品和服務，滿足不同客戶的需求。公司注重創新和品質。",
            "products": "產品A、產品B、產品C、產品D",
            "trade": "綜合業",
            "optimization_mode": "STANDARD",
            "word_limit": 300,
            "capital": 100000000,
            "employee_count": 1000,
            "established_year": 1995,
        },
        "checks": ["response_time", "format", "china_terms", "info_usage"],
        "expected_keywords": ["1億", "1000", "1995"],
    },
]


# ==================== 輔助函數 ====================
def count_chinese_characters(text: str) -> int:
    """計算中文字數"""
    if not text:
        return 0
    clean_text = BeautifulSoup(text, "html.parser").get_text()
    return len(clean_text)


def check_punctuation_consistency(text: str) -> Dict[str, Any]:
    """檢查標點符號一致性"""
    issues = []

    # 檢查中英文標點混用
    chinese_punctuation = ["，", "。", "！", "？", "；", "：", "、"]
    english_punctuation = [",", ".", "!", "?", ";", ":"]

    has_chinese = any(p in text for p in chinese_punctuation)
    has_english = any(p in text for p in english_punctuation)

    if has_chinese and has_english:
        issues.append("中英文標點符號混用")

    # 檢查多餘空格
    if re.search(r"  +", text):
        issues.append("存在多餘空格")

    # 檢查段落格式
    paragraphs = text.split("\n\n")
    empty_paragraphs = [p for p in paragraphs if not p.strip()]
    if empty_paragraphs:
        issues.append(f"存在 {len(empty_paragraphs)} 個空白段落")

    return {
        "issues": issues,
        "issue_count": len(issues),
        "passed": len(issues) == 0,
        "paragraph_count": len([p for p in paragraphs if p.strip()]),
    }


# ==================== 測試執行器 ====================
class Stage2Tester:
    """Stage 2 測試器"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.results: List[Dict] = []
        self.session = requests.Session()
        self.china_checker = ChinaTermChecker()

    def run_all_tests(self) -> List[Dict]:
        """執行所有測試"""
        print(f"\n🚀 開始執行 Stage 2 測試 ({len(TEST_CASES)} 個案例)...")
        print(f"   API 端點: {self.api_url}")
        print(f"   目標響應時間: <{Config.TARGET_RESPONSE_TIME}s")
        print(f"   目標資訊使用率: >{Config.TARGET_INFO_USAGE_RATE * 100:.0f}%")
        print()

        for test_case in TEST_CASES:
            result = self.run_single_test(test_case)
            self.results.append(result)

            status = "✅" if result["passed"] else "❌"
            api_status = "🟢" if result["api_success"] else "🔴"

            # 顯示關鍵指標
            time_str = f"{result['response_time']:.2f}s"
            usage_str = f"{result.get('info_usage_rate', 0) * 100:.0f}%"

            print(
                f"   {status} Case {result['case_id']:2d} | {api_status} | "
                f"{time_str:6s} | {usage_str:4s} | {result['name'][:25]:25s}"
            )

            if result.get("errors"):
                for error in result["errors"][:2]:  # 只顯示前2個錯誤
                    print(f"      ⚠️  {error}")

        return self.results

    def run_single_test(self, test_case: Dict) -> Dict:
        """執行單一測試"""
        case_id = test_case["case_id"]
        request_data = test_case["input"].copy()
        checks = test_case.get("checks", [])
        expected_keywords = test_case.get("expected_keywords", [])

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
            "checks": {},
        }

        try:
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

                content_plain = response_data.get("content_plain", "")
                content_html = response_data.get("body_html", "")

                result["content_length"] = count_chinese_characters(content_plain)

                # 檢查 1: 響應時間
                if "response_time" in checks:
                    time_check = result["response_time"] <= Config.TARGET_RESPONSE_TIME
                    result["checks"]["response_time"] = {
                        "passed": time_check,
                        "actual": result["response_time"],
                        "target": Config.TARGET_RESPONSE_TIME,
                    }
                    if not time_check:
                        result["warnings"].append(
                            f"響應時間 {result['response_time']:.2f}s 超過目標 {Config.TARGET_RESPONSE_TIME}s"
                        )

                # 檢查 2: 中國用語
                if "china_terms" in checks:
                    china_check = self.china_checker.check_text(content_plain)
                    result["checks"]["china_terms"] = china_check

                    if china_check["risk_level"] != "none":
                        result["warnings"].append(
                            f"發現 {china_check['total_issues']} 個中國用語問題"
                        )

                # 檢查 3: 格式一致性
                if "format" in checks or "punctuation" in checks:
                    format_check = check_punctuation_consistency(content_plain)
                    result["checks"]["format"] = format_check

                    if not format_check["passed"]:
                        result["warnings"].append(
                            f"格式問題: {', '.join(format_check['issues'])}"
                        )

                # 檢查 4: 資訊使用率
                if "info_usage" in checks and expected_keywords:
                    found_keywords = []
                    for kw in expected_keywords:
                        if kw in content_plain:
                            found_keywords.append(kw)

                    usage_rate = len(found_keywords) / len(expected_keywords)
                    result["info_usage_rate"] = usage_rate
                    result["found_keywords"] = found_keywords
                    result["expected_keywords"] = expected_keywords

                    usage_passed = usage_rate >= Config.TARGET_INFO_USAGE_RATE
                    result["checks"]["info_usage"] = {
                        "passed": usage_passed,
                        "rate": usage_rate,
                        "found": len(found_keywords),
                        "total": len(expected_keywords),
                    }

                    if not usage_passed:
                        result["warnings"].append(
                            f"資訊使用率 {usage_rate * 100:.0f}% 低於目標 {Config.TARGET_INFO_USAGE_RATE * 100:.0f}%"
                        )

                # 判定通過：API 成功且無嚴重錯誤
                result["passed"] = len(result["errors"]) == 0

            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg += f": {error_data['message']}"
                except:
                    error_msg += f": {response.text[:100]}"

                result["errors"].append(error_msg)
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

        # 響應時間統計
        response_times = [r["response_time"] for r in self.results if r["api_success"]]
        avg_time = sum(response_times) / len(response_times) if response_times else 0
        min_time = min(response_times) if response_times else 0
        max_time = max(response_times) if response_times else 0

        # 檢查有多少達到目標響應時間
        time_target_met = sum(
            1
            for r in self.results
            if r["api_success"] and r["response_time"] <= Config.TARGET_RESPONSE_TIME
        )

        # 中國用語統計
        china_risk_high = sum(
            1
            for r in self.results
            if r.get("checks", {}).get("china_terms", {}).get("risk_level") == "high"
        )
        china_risk_medium = sum(
            1
            for r in self.results
            if r.get("checks", {}).get("china_terms", {}).get("risk_level") == "medium"
        )

        # 資訊使用率統計
        info_usage_rates = [
            r.get("info_usage_rate", 0) for r in self.results if "info_usage_rate" in r
        ]
        avg_usage_rate = (
            sum(info_usage_rates) / len(info_usage_rates) if info_usage_rates else 0
        )

        return {
            "total_tests": total,
            "api_success": api_success,
            "api_failed": total - api_success,
            "passed": passed,
            "failed": total - passed,
            "success_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "N/A",
            "avg_response_time": f"{avg_time:.2f}s",
            "min_response_time": f"{min_time:.2f}s",
            "max_response_time": f"{max_time:.2f}s",
            "time_target_met": f"{time_target_met}/{api_success}",
            "time_target_rate": f"{(time_target_met / api_success * 100):.1f}%"
            if api_success > 0
            else "N/A",
            "china_risk_high": china_risk_high,
            "china_risk_medium": china_risk_medium,
            "avg_info_usage_rate": f"{avg_usage_rate * 100:.1f}%",
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
            "test_suite": "Phase 14 Stage 2 - 核心功能測試",
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
                ["案例ID", "名稱", "響應時間", "資訊使用率", "中國用語風險", "狀態"]
            )

            for r in self.results:
                china_risk = (
                    r.get("checks", {}).get("china_terms", {}).get("risk_level", "none")
                )
                usage_rate = r.get("info_usage_rate", 0) * 100

                writer.writerow(
                    [
                        r["case_id"],
                        r["name"],
                        f"{r['response_time']:.2f}s",
                        f"{usage_rate:.0f}%" if usage_rate > 0 else "N/A",
                        china_risk,
                        "PASS" if r["passed"] else "FAIL",
                    ]
                )
        print(f"   ✅ CSV 報告: {Config.TEST_CSV}")

    def _generate_excel_report(self):
        """生成 Excel 報告"""
        # Sheet 1: 測試結果
        data = []
        for r in self.results:
            china_check = r.get("checks", {}).get("china_terms", {})
            format_check = r.get("checks", {}).get("format", {})

            row = {
                "案例ID": r["case_id"],
                "測試名稱": r["name"],
                "響應時間": f"{r['response_time']:.2f}s",
                "內容長度": r.get("content_length", "N/A"),
                "資訊使用率": f"{r.get('info_usage_rate', 0) * 100:.1f}%"
                if r.get("info_usage_rate")
                else "N/A",
                "中國用語風險": china_check.get("risk_level", "none"),
                "格式問題數": format_check.get("issue_count", 0),
                "狀態": "✅ 通過" if r["passed"] else "❌ 失敗",
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Sheet 2: 摘要
        summary_data = {
            "項目": [
                "總測試數",
                "API成功",
                "通過數",
                "失敗數",
                "成功率",
                "平均響應時間",
                "響應時間目標達成率",
                "高中國用語風險案例",
                "平均資訊使用率",
            ],
            "結果": [
                self.summary["total_tests"],
                self.summary["api_success"],
                self.summary["passed"],
                self.summary["failed"],
                self.summary["success_rate"],
                self.summary["avg_response_time"],
                self.summary["time_target_rate"],
                self.summary["china_risk_high"],
                self.summary["avg_info_usage_rate"],
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
    parser = argparse.ArgumentParser(description="Phase 14 Stage 2 - 核心功能測試")
    parser.add_argument(
        "--api-url", default=Config.DEFAULT_API_URL, help="API 端點 URL"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 14 Stage 2 - 核心功能測試")
    print("=" * 80)
    print(f"\n測試項目:")
    print(f"  • 輸入資訊使用率 (目標: >{Config.TARGET_INFO_USAGE_RATE * 100:.0f}%)")
    print(f"  • 中國用語檢測")
    print(f"  • 格式一致性檢查")
    print(f"  • 性能基準 (目標: <{Config.TARGET_RESPONSE_TIME}s)")

    # 執行測試
    tester = Stage2Tester(args.api_url)
    results = tester.run_all_tests()

    # 生成摘要
    summary = tester.generate_summary()

    # 生成報告
    generator = ReportGenerator(results, summary)
    generator.generate_all_reports()

    # 顯示結果摘要
    print("\n" + "=" * 80)
    print("📊 Stage 2 測試結果摘要")
    print("=" * 80)
    print(f"\n總測試數: {summary['total_tests']}")
    print(f"API 成功: {summary['api_success']}")
    print(f"通過: {summary['passed']} | 失敗: {summary['failed']}")
    print(f"成功率: {summary['success_rate']}")

    print(f"\n⏱️  性能指標:")
    print(f"  平均響應時間: {summary['avg_response_time']}")
    print(f"  範圍: {summary['min_response_time']} - {summary['max_response_time']}")
    print(
        f"  目標達成率 (<{Config.TARGET_RESPONSE_TIME}s): {summary['time_target_rate']}"
    )

    print(f"\n📝 質量指標:")
    print(f"  高中國用語風險案例: {summary['china_risk_high']}")
    print(f"  中國用語風險案例: {summary['china_risk_medium']}")
    print(f"  平均資訊使用率: {summary['avg_info_usage_rate']}")

    # Phase 14 階段二目標評估
    print("\n" + "=" * 80)
    print("🎯 Phase 14 階段二目標評估")
    print("=" * 80)

    # 目標 1: 生成速度 <5秒 (已達成，Stage 2 目標 <2秒)
    avg_time = float(summary["avg_response_time"].replace("s", ""))
    time_passed = avg_time < Config.TARGET_RESPONSE_TIME
    print(f"\n{'✅' if time_passed else '❌'} 生成速度優化")
    print(
        f"   目標: <{Config.TARGET_RESPONSE_TIME}s | 實際: {summary['avg_response_time']}"
    )

    # 目標 2: 輸入資訊使用率 80%
    avg_usage = float(summary["avg_info_usage_rate"].replace("%", ""))
    usage_passed = avg_usage >= Config.TARGET_INFO_USAGE_RATE * 100
    print(f"\n{'✅' if usage_passed else '❌'} 輸入資訊使用率")
    print(
        f"   目標: >{Config.TARGET_INFO_USAGE_RATE * 100:.0f}% | 實際: {summary['avg_info_usage_rate']}"
    )

    # 目標 3: 無中國用語
    china_passed = summary["china_risk_high"] == 0
    print(f"\n{'✅' if china_passed else '⚠️ '} 中國用語檢查")
    print(f"   高中國用語風險案例: {summary['china_risk_high']}")

    # 目標 4: 格式一致
    format_issues = sum(
        r.get("checks", {}).get("format", {}).get("issue_count", 0) for r in results
    )
    format_passed = format_issues == 0
    print(f"\n{'✅' if format_passed else '⚠️ '} 格式一致性")
    print(f"   格式問題總數: {format_issues}")

    # 整體評估
    all_passed = time_passed and usage_passed and china_passed and format_passed

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 Phase 14 Stage 2: ✅ 所有目標達成！")
    else:
        print("⚠️  Phase 14 Stage 2: 部分目標待優化")
        print("\n待優化項目:")
        if not time_passed:
            print("  • 響應時間需要優化")
        if not usage_passed:
            print("  • 資訊使用率需要提升")
        if not china_passed:
            print("  • 中國用語需要修正")
        if not format_passed:
            print("  • 格式一致性需要改進")

    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
