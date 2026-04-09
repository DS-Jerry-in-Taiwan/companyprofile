"""
自動化測試腳本 - 基於實際用戶測試報告
測試數據來自: test_20260407.pdf 和 test_20260408.pdf

這個腳本會模擬前端用戶的操作，自動填寫表單並驗證結果
"""

import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

# 配置
API_BASE_URL = "http://localhost:5000"
API_ENDPOINT = f"{API_BASE_URL}/v1/company/profile/process"


class TestCase:
    """測試用例數據結構"""

    def __init__(
        self,
        case_id: int,
        name: str,
        input_data: Dict[str, Any],
        expected_validation: Dict[str, Any],
    ):
        self.case_id = case_id
        self.name = name
        self.input_data = input_data
        self.expected_validation = expected_validation
        self.result = None
        self.error = None
        self.execution_time = 0


class AutomatedTestRunner:
    """自動化測試執行器"""

    def __init__(self):
        self.test_cases = []
        self.results = []
        self.report = {}

    def add_test_case(self, test_case: TestCase):
        """添加測試用例"""
        self.test_cases.append(test_case)

    def run_single_test(self, test_case: TestCase) -> Dict[str, Any]:
        """執行單個測試"""
        print(f"\n▶️  執行: {test_case.name}")
        print(
            f"   輸入: {json.dumps(test_case.input_data, ensure_ascii=False, indent=2)}"
        )

        start_time = time.time()
        try:
            response = requests.post(
                API_ENDPOINT, json=test_case.input_data, timeout=30
            )
            execution_time = time.time() - start_time

            # 驗證響應
            validation_result = self._validate_response(
                response, test_case.expected_validation, execution_time
            )

            test_case.result = response.json() if response.status_code == 200 else None
            test_case.execution_time = execution_time

            return validation_result

        except Exception as e:
            test_case.error = str(e)
            return {
                "case_id": test_case.case_id,
                "name": test_case.name,
                "status": "❌ 失敗",
                "error": str(e),
                "execution_time": 0,
            }

    def _validate_response(
        self, response, expected_validation: Dict[str, Any], execution_time: float
    ) -> Dict[str, Any]:
        """驗證API響應"""
        validations = {
            "case_id": response.status_code,
            "status_code": response.status_code,
            "execution_time": execution_time,
            "checks": [],
        }

        if response.status_code != 200:
            validations["status"] = "❌ HTTP 失敗"
            validations["error"] = response.text
            return validations

        data = response.json()
        all_pass = True

        # 檢查期望的驗證項
        for check_key, check_condition in expected_validation.items():
            check_result = self._check_condition(
                data, check_key, check_condition, execution_time
            )
            validations["checks"].append(check_result)
            if not check_result["pass"]:
                all_pass = False

        validations["status"] = "✅ 通過" if all_pass else "⚠️  部分失敗"
        return validations

    def _check_condition(
        self, data: Dict, key: str, condition: Any, execution_time: float
    ) -> Dict[str, Any]:
        """檢查單個驗證條件"""

        # 特殊檢查項
        if key == "response_time":
            passed = execution_time < condition
            return {
                "check": f"響應時間 < {condition}秒",
                "actual": f"{execution_time:.2f}秒",
                "pass": passed,
            }

        if key == "word_count":
            body = data.get("data", {}).get("body_html", "")
            actual_count = len(body)
            passed = actual_count <= condition
            return {
                "check": f"字數 <= {condition}",
                "actual": actual_count,
                "pass": passed,
            }

        if key == "no_verbose_phrases":
            body = data.get("data", {}).get("body_html", "")
            verbose_phrases = ["以下是", "根據", "以下是優化結果", "以下是生成"]
            found = [p for p in verbose_phrases if p in body]
            passed = len(found) == 0
            return {
                "check": "無冗言開頭",
                "found_phrases": found if found else "無",
                "pass": passed,
            }

        if key == "contains_optional_fields":
            body = data.get("data", {}).get("body_html", "")
            found_count = 0
            for field in condition:  # condition 是欄位列表
                if field in body:
                    found_count += 1
            passed = found_count >= len(condition) * 0.8  # 至少 80% 的欄位被使用
            return {
                "check": f"包含選填欄位信息 (至少 80%)",
                "expected_fields": condition,
                "found_count": found_count,
                "pass": passed,
            }

        # 通用檢查
        actual_value = data.get(key)
        passed = (
            actual_value == condition if isinstance(condition, str) else actual_value
        )
        return {"check": f"{key} = {condition}", "actual": actual_value, "pass": passed}

    def run_all_tests(self):
        """執行所有測試"""
        print("\n" + "=" * 80)
        print("🧪 開始執行自動化測試")
        print("=" * 80)

        for test_case in self.test_cases:
            result = self.run_single_test(test_case)
            self.results.append(result)

        self._generate_report()

    def _generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 80)
        print("📊 測試報告摘要")
        print("=" * 80)

        passed = sum(1 for r in self.results if r.get("status", "").startswith("✅"))
        failed = sum(1 for r in self.results if r.get("status", "").startswith("❌"))
        partial = sum(1 for r in self.results if r.get("status", "").startswith("⚠️"))

        print(f"\n結果統計:")
        print(f"  ✅ 完全通過: {passed}")
        print(f"  ⚠️  部分失敗: {partial}")
        print(f"  ❌ 完全失敗: {failed}")
        print(f"  總計: {len(self.results)}")

        print(
            f"\n成功率: {(passed / len(self.results) * 100):.1f}%"
            if self.results
            else "N/A"
        )

        # 詳細結果
        print("\n詳細檢查結果:")
        for result in self.results:
            print(f"\n  測試用例 #{result['case_id']}: {result.get('status', '?')}")
            if result.get("error"):
                print(f"    錯誤: {result['error']}")
            else:
                print(f"    執行時間: {result['execution_time']:.2f}秒")
                for check in result.get("checks", []):
                    status = "✓" if check["pass"] else "✗"
                    print(f"    {status} {check['check']}")
                    if not check["pass"]:
                        print(f"       實際: {check.get('actual')}")


# ============================================================================
# 根據實際測試報告設計的測試用例
# ============================================================================


def create_test_cases() -> List[TestCase]:
    """根據 test_20260407.pdf 和 test_20260408.pdf 創建測試用例"""

    test_cases = []

    # 【問題1】選填欄位無反應測試
    test_cases.append(
        TestCase(
            case_id=1,
            name="選填欄位測試 - 資本額 + 員工人數",
            input_data={
                "mode": "GENERATE",
                "organNo": "12345678",
                "organ": "科技公司 A",
                "capital": 5000,  # 資本額 5000 萬
                "employees": 100,  # 員工人數 100 人
                "word_limit": 200,
            },
            expected_validation={
                "response_time": 10,  # 應在 10 秒內響應
                "word_count": 200,  # 字數限制 200 字
                "contains_optional_fields": ["5000", "100"],  # 應包含這些信息
            },
        )
    )

    test_cases.append(
        TestCase(
            case_id=2,
            name="選填欄位測試 - 所有選填欄位",
            input_data={
                "mode": "GENERATE",
                "organNo": "87654321",
                "organ": "製造公司 B",
                "capital": 10000,  # 資本額 1 億
                "employees": 500,  # 員工人數 500 人
                "founded_year": 2015,  # 成立年份 2015 年
                "word_limit": 300,
            },
            expected_validation={
                "response_time": 10,
                "word_count": 300,
                "contains_optional_fields": ["10000", "500", "2015"],
            },
        )
    )

    # 【問題2】字數限制測試
    test_cases.append(
        TestCase(
            case_id=3,
            name="字數限制測試 - 50字",
            input_data={
                "mode": "GENERATE",
                "organNo": "11111111",
                "organ": "服務公司 C",
                "word_limit": 50,  # 限制 50 字
            },
            expected_validation={
                "response_time": 10,
                "word_count": 50,  # 應正確限制在 50 字以內
            },
        )
    )

    test_cases.append(
        TestCase(
            case_id=4,
            name="字數限制測試 - 100字",
            input_data={
                "mode": "GENERATE",
                "organNo": "22222222",
                "organ": "工程公司 D",
                "word_limit": 100,  # 限制 100 字
            },
            expected_validation={
                "response_time": 10,
                "word_count": 100,  # 應正確限制在 100 字以內
            },
        )
    )

    test_cases.append(
        TestCase(
            case_id=5,
            name="字數限制測試 - 200字",
            input_data={
                "mode": "GENERATE",
                "organNo": "33333333",
                "organ": "咨詢公司 E",
                "word_limit": 200,  # 限制 200 字
            },
            expected_validation={"response_time": 10, "word_count": 200},
        )
    )

    # 【問題3】冗言開頭測試
    test_cases.append(
        TestCase(
            case_id=6,
            name="冗言移除測試 - 檢查生成結果開頭",
            input_data={
                "mode": "GENERATE",
                "organNo": "44444444",
                "organ": "軟件公司 F",
                "word_limit": 150,
            },
            expected_validation={
                "response_time": 10,
                "word_count": 150,
                "no_verbose_phrases": True,  # 應無冗言開頭
            },
        )
    )

    # 【邊界測試】各種邊界條件
    test_cases.append(
        TestCase(
            case_id=7,
            name="邊界測試 - 最小字數 (50字)",
            input_data={
                "mode": "GENERATE",
                "organNo": "55555555",
                "organ": "初創公司 G",
                "word_limit": 50,
            },
            expected_validation={"response_time": 10, "word_count": 50},
        )
    )

    test_cases.append(
        TestCase(
            case_id=8,
            name="邊界測試 - 最大字數 (300字)",
            input_data={
                "mode": "GENERATE",
                "organNo": "66666666",
                "organ": "大型集團 H",
                "word_limit": 300,
            },
            expected_validation={"response_time": 10, "word_count": 300},
        )
    )

    test_cases.append(
        TestCase(
            case_id=9,
            name="邊界測試 - 無選填欄位",
            input_data={
                "mode": "GENERATE",
                "organNo": "77777777",
                "organ": "標準公司 I",
            },
            expected_validation={"response_time": 10},
        )
    )

    test_cases.append(
        TestCase(
            case_id=10,
            name="邊界測試 - 所有選填欄位 + 最小字數",
            input_data={
                "mode": "GENERATE",
                "organNo": "88888888",
                "organ": "複雜公司 J",
                "capital": 1000,
                "employees": 10,
                "founded_year": 2020,
                "word_limit": 50,
            },
            expected_validation={"response_time": 10, "word_count": 50},
        )
    )

    return test_cases


def main():
    """主函數"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║     自動化測試 - 基於實際用戶測試報告 (test_20260407/08)                  ║
║     目的: 驗證三個最高優先級問題是否已修復                                ║
║     - 問題1: 選填欄位無反應                                                ║
║     - 問題2: 字數限制失效                                                  ║
║     - 問題3: 開頭冗言                                                      ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # 檢查 API 連接
    print("🔍 檢查 API 連接...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API 已連接")
        else:
            print("❌ API 響應異常")
            return
    except Exception as e:
        print(f"❌ 無法連接到 API: {e}")
        print(f"   請確保後端運行在 {API_BASE_URL}")
        return

    # 創建並運行測試
    runner = AutomatedTestRunner()
    test_cases = create_test_cases()

    for test_case in test_cases:
        runner.add_test_case(test_case)

    runner.run_all_tests()

    # 保存報告
    report_file = "test_results.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(runner.results),
                "results": runner.results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n📄 詳細報告已保存到: {report_file}")


if __name__ == "__main__":
    main()
