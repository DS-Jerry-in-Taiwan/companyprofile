#!/usr/bin/env python3
"""
Phase 14 Checkpoint 1 - 完整測試腳本 (合併版)
=============================================
整合 Input 結構化 + API 自動化測試 + Excel 報告產出

使用方法:
  python3 complete_checkpoint1_test.py [--api-url URL]

流程:
  1. 讀取 Excel 測試資料
  2. 生成標準化輸入文件 (JSON/CSV/MD)
  3. 執行 API 自動化測試 (10個案例)
  4. 驗證 Bug C (冗餘短語) 和 Bug D (響應時間)
  5. 生成完整測試報告 (JSON/CSV/MD/Excel)

輸出文件:
  - test_inputs.json                    # 標準化測試輸入
  - test_inputs_api.json               # API 測試格式
  - test_inputs_summary.csv            # 輸入摘要表格
  - checkpoint1_test_report.json       # 詳細測試結果
  - checkpoint1_test_report.md         # 可讀報告
  - checkpoint1_summary.csv            # 測試摘要
  - checkpoint1_automated_test_results.xlsx  # ⭐ Excel 完整報告
"""

import pandas as pd
import json
import re
import time
import csv
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from html.parser import HTMLParser
import requests


# ==================== 配置 ====================
class Config:
    # 輸入文件
    INPUT_XLSX = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/checkpoint1/artifacts/1111_公司簡介生成優化.xlsx"
    )

    # 輸出目錄
    OUTPUT_DIR = Path(
        "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/checkpoint1/artifacts"
    )

    # 確保輸出目錄存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 輸入階段輸出文件
    INPUT_STANDARD = OUTPUT_DIR / "test_inputs.json"
    INPUT_API = OUTPUT_DIR / "test_inputs_api.json"
    INPUT_CSV = OUTPUT_DIR / "test_inputs_summary.csv"
    INPUT_MD = OUTPUT_DIR / "test_inputs_report.md"

    # 測試階段輸出文件
    TEST_JSON = OUTPUT_DIR / "checkpoint1_test_report.json"
    TEST_MD = OUTPUT_DIR / "checkpoint1_test_report.md"
    TEST_CSV = OUTPUT_DIR / "checkpoint1_summary.csv"

    # ⭐ Excel 報告
    TEST_EXCEL = OUTPUT_DIR / "checkpoint1_automated_test_results.xlsx"

    # API 配置
    DEFAULT_API_URL = "http://localhost:5000/v1/company/profile/process"
    TIMEOUT_SECONDS = 30
    MAX_RESPONSE_TIME = 5.0

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


# ==================== 數據模型 ====================
class TestInput:
    """標準化測試輸入"""

    def __init__(self, case_id: int):
        self.case_id = case_id
        self.company_name: str = ""
        self.company_id: str = ""
        self.industry_type: str = ""
        self.industry_code: str = ""
        self.product_service: str = ""
        self.before_text: str = ""
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "company": {
                "name": self.company_name,
                "registration_id": self.company_id,
                "industry": {"type": self.industry_type, "code": self.industry_code},
            },
            "product_service": self.product_service,
            "input_text": self.before_text,
            "text_stats": {
                "char_count": len(self.before_text),
                "chinese_char_count": len(
                    re.findall(r"[\u4e00-\u9fff]", self.before_text)
                ),
                "line_count": len(self.before_text.split("\n")),
            },
            "metadata": self.metadata,
        }

    def to_api_format(self) -> Dict[str, Any]:
        """轉換為 API 請求格式"""
        return {
            "mode": "GENERATE",
            "organ": self.company_name,
            "organNo": self.company_id,
            "brief": self.before_text,
            "products": self.product_service,
            "trade": self.industry_type,
            "optimization_mode": "STANDARD",
            "word_limit": None,
        }


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


# ==================== Excel 解析器 (Input 階段) ====================
class ExcelParser:
    """Excel 測試數據解析器"""

    def __init__(self, xlsx_path: Path):
        self.xlsx_path = xlsx_path
        self.df: Optional[pd.DataFrame] = None
        self.inputs: List[TestInput] = []

    def load(self) -> bool:
        """載入 Excel 文件"""
        try:
            self.df = pd.read_excel(self.xlsx_path)
            print(f"✅ Excel 載入成功: {len(self.df)} 行, {len(self.df.columns)} 欄位")
            return True
        except Exception as e:
            print(f"❌ Excel 載入失敗: {e}")
            return False

    def parse(self) -> List[TestInput]:
        """解析測試輸入數據"""
        if self.df is None:
            return []

        df = self.df.fillna("")
        current_input = None

        for idx, row in df.iterrows():
            if row["案例"] != "" and row["案例"] != 0:
                company_info = str(row["廠商名稱 & 編號"]).split("\n")
                company_name = company_info[0].strip() if len(company_info) > 0 else ""
                company_id = company_info[1].strip() if len(company_info) > 1 else ""

                industry_info = str(row["產業類型 & 代碼"]).split("\n")
                industry_type = (
                    industry_info[0].strip() if len(industry_info) > 0 else ""
                )
                industry_code = (
                    industry_info[1].strip() if len(industry_info) > 1 else ""
                )

                case_id = int(row["案例"])
                current_input = TestInput(case_id)
                current_input.company_name = company_name
                current_input.company_id = company_id
                current_input.industry_type = industry_type
                current_input.industry_code = industry_code
                current_input.product_service = str(row["產品/服務"]).strip()
                current_input.before_text = str(row["公司簡介 - before"]).strip()
                current_input.metadata = {
                    "row_index": idx,
                    "excel_file": str(self.xlsx_path.name),
                }

                self.inputs.append(current_input)

        print(f"✅ 解析完成: {len(self.inputs)} 個測試輸入案例")
        return self.inputs

    def get_summary(self) -> Dict[str, Any]:
        """獲取數據摘要"""
        if not self.inputs:
            return {}

        total_chars = sum(len(inp.before_text) for inp in self.inputs)
        total_chinese = sum(
            len(re.findall(r"[\u4e00-\u9fff]", inp.before_text)) for inp in self.inputs
        )

        return {
            "total_cases": len(self.inputs),
            "companies": [inp.company_name for inp in self.inputs],
            "industries": list(set(inp.industry_type for inp in self.inputs)),
            "avg_text_length": total_chars / len(self.inputs) if self.inputs else 0,
            "avg_chinese_chars": total_chinese / len(self.inputs) if self.inputs else 0,
            "total_chinese_chars": total_chinese,
        }


# ==================== API 測試器 ====================
class APITester:
    """API 自動化測試器"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.results: List[TestResult] = []
        self.session = requests.Session()

    def run_all_tests(self, test_cases: List[Dict]) -> List[TestResult]:
        """執行所有測試"""
        print(f"\n🚀 開始執行 {len(test_cases)} 個測試案例...")
        print(f"   API 端點: {self.api_url}")
        print()

        for i, test_case in enumerate(test_cases, 1):
            result = self.run_single_test(test_case)
            self.results.append(result)

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
            start_time = time.time()
            response = self.session.post(
                self.api_url, json=request_data, timeout=Config.TIMEOUT_SECONDS
            )
            result.response_time = time.time() - start_time

            if response.status_code == 200:
                result.response_data = response.json()
                result.success = True
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
            if re.search(pattern, output_text[:200]):
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

        avg_time = (
            sum(r.response_time for r in self.results) / total if total > 0 else 0
        )

        verbose_issues = sum(
            1
            for r in self.results
            if not r.validation_results.get("verbose_phrase_check", {}).get(
                "passed", True
            )
        )

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
            "failed": total - successful,
            "success_rate": f"{(successful / total * 100):.1f}%"
            if total > 0
            else "N/A",
            "avg_response_time": f"{avg_time:.2f}s",
            "bug_c_verbose_phrases": verbose_issues,
            "bug_d_slow_responses": slow_responses,
            "generated_at": datetime.now().isoformat(),
        }


# ==================== 報告生成器 ====================
class ReportGenerator:
    """測試報告生成器"""

    def __init__(
        self, inputs: List[TestInput], results: List[TestResult], summary: Dict
    ):
        self.inputs = inputs
        self.results = results
        self.summary = summary

    def _strip_html_tags(self, html_text: str) -> str:
        """去除 HTML 標籤，返回純文本"""
        if not html_text:
            return ""

        # 簡單的 HTML 標籤去除
        # 先處理 <p> 和 <a> 標籤
        text = html_text

        # 將 </p> 替換為換行
        text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<p[^>]*>", "", text, flags=re.IGNORECASE)

        # 將 <a> 標籤轉換為 "文本(網址)" 格式
        text = re.sub(
            r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            r"\2(\1)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # 去除其他所有 HTML 標籤
        text = re.sub(r"<[^>]+>", "", text)

        # 去除多餘的空白行
        text = re.sub(r"\n\n\n+", "\n\n", text)

        return text.strip()

    def generate_all_reports(self):
        """生成所有報告文件"""
        print("\n📝 正在生成報告...")

        # 1. 輸入階段報告
        self._generate_input_reports()

        # 2. 測試階段報告
        self._generate_test_reports()

        # 3. ⭐ Excel 完整報告
        self._generate_excel_report()

        print(f"\n✅ 所有報告已保存到: {Config.OUTPUT_DIR}")

    def _generate_input_reports(self):
        """生成輸入階段報告"""
        summary = {
            "total_cases": len(self.inputs),
            "avg_text_length": sum(len(inp.before_text) for inp in self.inputs)
            / len(self.inputs)
            if self.inputs
            else 0,
            "avg_chinese_chars": sum(
                len(re.findall(r"[\u4e00-\u9fff]", inp.before_text))
                for inp in self.inputs
            )
            / len(self.inputs)
            if self.inputs
            else 0,
        }

        # JSON
        standard_output = {
            "document": "1111_公司簡介測試輸入",
            "generated_at": datetime.now().isoformat(),
            "source_file": str(Config.INPUT_XLSX.name),
            "summary": summary,
            "test_inputs": [inp.to_dict() for inp in self.inputs],
        }

        with open(Config.INPUT_STANDARD, "w", encoding="utf-8") as f:
            json.dump(standard_output, f, ensure_ascii=False, indent=2)
        print(f"   ✅ 標準 JSON: {Config.INPUT_STANDARD}")

        # API JSON
        api_output = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "test_cases": [
                {"case_id": inp.case_id, "request": inp.to_api_format()}
                for inp in self.inputs
            ],
        }

        with open(Config.INPUT_API, "w", encoding="utf-8") as f:
            json.dump(api_output, f, ensure_ascii=False, indent=2)
        print(f"   ✅ API 格式 JSON: {Config.INPUT_API}")

        # CSV
        with open(Config.INPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["案例ID", "廠商名稱", "統編", "產業類型", "輸入字數", "中文字數"]
            )
            for inp in self.inputs:
                chinese_count = len(re.findall(r"[\u4e00-\u9fff]", inp.before_text))
                writer.writerow(
                    [
                        inp.case_id,
                        inp.company_name,
                        inp.company_id,
                        inp.industry_type,
                        len(inp.before_text),
                        chinese_count,
                    ]
                )
        print(f"   ✅ CSV 摘要: {Config.INPUT_CSV}")

    def _generate_test_reports(self):
        """生成測試階段報告"""
        # JSON
        report = {
            "test_suite": "Phase 14 Checkpoint 1",
            "summary": self.summary,
            "test_results": [r.to_dict() for r in self.results],
        }

        with open(Config.TEST_JSON, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"   ✅ JSON 報告: {Config.TEST_JSON}")

        # CSV
        with open(Config.TEST_CSV, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["案例ID", "狀態", "回應時間", "字數", "冗餘短語", "錯誤數"]
            )
            for r in self.results:
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
        print(f"   ✅ CSV 報告: {Config.TEST_CSV}")

    def _generate_excel_report(self):
        """⭐ 生成 Excel 報告 - 完全符合 1111_公司簡介生成優化.xlsx 格式"""
        print(f"\n📊 正在生成 Excel 報告 (符合原始格式)...")

        # 準備數據 - 完全符合原始 Excel 格式 (8個欄位)
        data = []
        for i, inp in enumerate(self.inputs):
            result = self.results[i] if i < len(self.results) else None

            if result and result.success:
                response_data = result.response_data

                # 使用 content_plain（純文本，無 HTML 標籤）
                # 優先順序：content_plain > content_paragraphs (joined) > body_html (fallback)
                if response_data.get("content_plain"):
                    after_text = response_data.get("content_plain", "")
                elif response_data.get("content_paragraphs"):
                    after_text = "\n\n".join(
                        response_data.get("content_paragraphs", [])
                    )
                else:
                    # 後備：使用 body_html 並嘗試去除 HTML 標籤
                    after_text = self._strip_html_tags(
                        response_data.get("body_html", "")
                    )

                # 完全符合原始 Excel 格式的 8 個欄位
                row = {
                    "案例": float(inp.case_id),  # 使用浮點數，如 1.0, 2.0
                    "廠商名稱 & 編號": f"{inp.company_name}\n{inp.company_id}",
                    "產業類型 & 代碼": f"{inp.industry_type}\n{inp.industry_code}",
                    "產品/服務": inp.product_service,
                    "公司簡介 - before": inp.before_text,
                    "公司簡介 - after": after_text,
                    "Optimisation Mode": 1,  # 數字 1 (代表 STANDARD)
                    "Response Time": f"{result.response_time:.2f} s",
                }
            else:
                row = {
                    "案例": float(inp.case_id),
                    "廠商名稱 & 編號": f"{inp.company_name}\n{inp.company_id}",
                    "產業類型 & 代碼": f"{inp.industry_type}\n{inp.industry_code}",
                    "產品/服務": inp.product_service,
                    "公司簡介 - before": inp.before_text,
                    "公司簡介 - after": f"ERROR: {result.errors[0] if result and result.errors else 'Unknown'}",
                    "Optimisation Mode": 1,
                    "Response Time": f"{result.response_time:.2f} s"
                    if result
                    else "0.00 s",
                }

            data.append(row)

        # 創建 DataFrame - 確保欄位順序與原始 Excel 一致
        df = pd.DataFrame(
            data,
            columns=[
                "案例",
                "廠商名稱 & 編號",
                "產業類型 & 代碼",
                "產品/服務",
                "公司簡介 - before",
                "公司簡介 - after",
                "Optimisation Mode",
                "Response Time",
            ],
        )

        # 保存到 Excel
        with pd.ExcelWriter(Config.TEST_EXCEL, engine="openpyxl") as writer:
            # Sheet 1: 測試結果 (符合原始格式)
            df.to_excel(writer, sheet_name="測試結果", index=False)

            # 調整欄寬
            worksheet = writer.sheets["測試結果"]
            column_widths = {
                "A": 8,  # 案例
                "B": 25,  # 廠商名稱 & 編號
                "C": 20,  # 產業類型 & 代碼
                "D": 30,  # 產品/服務
                "E": 50,  # 公司簡介 - before
                "F": 50,  # 公司簡介 - after
                "G": 18,  # Optimisation Mode
                "H": 15,  # Response Time
            }
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

            # Sheet 2: 測試摘要 (額外的摘要頁)
            summary_data = {
                "項目": [
                    "總案例數",
                    "成功",
                    "失敗",
                    "成功率",
                    "平均響應時間",
                    "Bug C (冗餘短語) 問題數",
                    "Bug D (響應時間超標) 問題數",
                    "Checkpoint 1 狀態",
                ],
                "結果": [
                    self.summary["total_tests"],
                    self.summary["successful"],
                    self.summary["failed"],
                    self.summary["success_rate"],
                    self.summary["avg_response_time"],
                    self.summary["bug_c_verbose_phrases"],
                    self.summary["bug_d_slow_responses"],
                    "PASSED ✅"
                    if self.summary["bug_c_verbose_phrases"] == 0
                    and self.summary["success_rate"] == "100.0%"
                    else "NEED ATTENTION ⚠️",
                ],
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="測試摘要", index=False)

            # 調整摘要欄寬
            worksheet2 = writer.sheets["測試摘要"]
            worksheet2.column_dimensions["A"].width = 30
            worksheet2.column_dimensions["B"].width = 20

        print(f"   ✅ Excel 報告: {Config.TEST_EXCEL}")
        print(f"      - Sheet 1: 測試結果 ({len(df)} 行, 8個欄位)")
        print(f"      - Sheet 2: 測試摘要")


# ==================== 主程式 ====================
def main():
    parser = argparse.ArgumentParser(description="Phase 14 Checkpoint 1 - 完整測試腳本")
    parser.add_argument(
        "--api-url", default=Config.DEFAULT_API_URL, help="API 端點 URL"
    )
    parser.add_argument(
        "--input-only", action="store_true", help="只生成輸入文件，不執行 API 測試"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 14 Checkpoint 1 - 完整測試腳本")
    print("=" * 80)

    # ========== 階段 1: Input 結構化 ==========
    print("\n📋 階段 1: Input 結構化")
    print("-" * 80)

    if not Config.INPUT_XLSX.exists():
        print(f"❌ 找不到輸入文件: {Config.INPUT_XLSX}")
        return 1

    parser = ExcelParser(Config.INPUT_XLSX)
    if not parser.load():
        return 1

    inputs = parser.parse()
    if not inputs:
        print("❌ 未找到有效的測試輸入數據")
        return 1

    print(f"✅ 解析完成: {len(inputs)} 個測試案例")

    if args.input_only:
        # 只生成輸入報告
        generator = ReportGenerator(inputs, [], {})
        generator._generate_input_reports()
        print("\n✅ 輸入文件生成完成！")
        return 0

    # ========== 階段 2: API 自動化測試 ==========
    print("\n🚀 階段 2: API 自動化測試")
    print("-" * 80)

    tester = APITester(args.api_url)

    # 載入測試案例
    test_cases = [
        {"case_id": inp.case_id, "request": inp.to_api_format()} for inp in inputs
    ]
    print(f"✅ 載入 {len(test_cases)} 個測試案例")

    # 執行測試
    results = tester.run_all_tests(test_cases)

    # 生成摘要
    summary = tester.generate_summary()

    # ========== 階段 3: 生成所有報告 ==========
    print("\n📝 階段 3: 生成測試報告")
    print("-" * 80)

    generator = ReportGenerator(inputs, results, summary)
    generator.generate_all_reports()

    # ========== 結果摘要 ==========
    print("\n" + "=" * 80)
    print("📊 Checkpoint 1 測試結果")
    print("=" * 80)
    print(f"\n總測試數: {summary['total_tests']}")
    print(f"成功: {summary['successful']}")
    print(f"失敗: {summary['failed']}")
    print(f"成功率: {summary['success_rate']}")
    print(f"\n平均響應時間: {summary['avg_response_time']}")
    print(f"Bug C (冗餘短語) 問題: {summary['bug_c_verbose_phrases']}")
    print(f"Bug D (響應時間) 問題: {summary['bug_d_slow_responses']}")

    # Checkpoint 1 狀態
    print("\n" + "=" * 80)
    checkpoint_pass = (
        summary["bug_c_verbose_phrases"] == 0 and summary["success_rate"] == "100.0%"
    )

    if checkpoint_pass:
        print("✅✅✅ CHECKPOINT 1 PASSED ✅✅✅")
        print("\n所有產出文件:")
        print(f"  📄 {Config.INPUT_STANDARD.name}")
        print(f"  📄 {Config.INPUT_API.name}")
        print(f"  📄 {Config.INPUT_CSV.name}")
        print(f"  📄 {Config.TEST_JSON.name}")
        print(f"  📄 {Config.TEST_CSV.name}")
        print(f"  📊 {Config.TEST_EXCEL.name} ⭐")
        print("\n🚀 可以進入 Stage 2！")
    else:
        print("⚠️  CHECKPOINT 1 需要關注:")
        if summary["bug_c_verbose_phrases"] > 0:
            print(f"   - Bug C: {summary['bug_c_verbose_phrases']} 個問題")
        if summary["failed"] > 0:
            print(f"   - API 錯誤: {summary['failed']} 個失敗")

    print("=" * 80)

    return 0 if checkpoint_pass else 1


if __name__ == "__main__":
    exit(main())
