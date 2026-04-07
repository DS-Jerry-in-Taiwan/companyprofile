#!/usr/bin/env python3
"""
E2E 測試補強腳本
根據 e2e_test_gap_list.md 識別的測試缺口，實作自動化測試腳本
"""

import pytest
import requests
import time
import json
import uuid
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class E2ETestFramework:
    """E2E 測試框架"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results: List[Dict[str, Any]] = []

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        headers: Dict = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """發送 HTTP 請求"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "POST":
                response = requests.post(
                    url, json=data, headers=headers, timeout=timeout
                )
            elif method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"不支援的 HTTP 方法: {method}")

            return {
                "status_code": response.status_code,
                "response_data": response.json() if response.content else {},
                "response_time": response.elapsed.total_seconds() * 1000,
                "success": True,
            }
        except requests.exceptions.Timeout:
            return {
                "status_code": 408,
                "response_data": {"error": "Request timeout"},
                "response_time": timeout * 1000,
                "success": False,
                "error": "Timeout",
            }
        except requests.exceptions.ConnectionError:
            return {
                "status_code": 0,
                "response_data": {"error": "Connection failed"},
                "response_time": 0,
                "success": False,
                "error": "Connection error",
            }
        except Exception as e:
            return {
                "status_code": 0,
                "response_data": {"error": str(e)},
                "response_time": 0,
                "success": False,
                "error": str(e),
            }

    def _record_test_result(
        self,
        test_name: str,
        result: Dict[str, Any],
        expected_status: int = 200,
        severity: str = "MEDIUM",
    ):
        """記錄測試結果"""
        test_result = {
            "test_name": test_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status_code": result["status_code"],
            "expected_status": expected_status,
            "response_time": result["response_time"],
            "success": result["success"] and result["status_code"] == expected_status,
            "severity": severity,
            "error": result.get("error"),
            "response_data": result["response_data"],
        }

        self.test_results.append(test_result)

        if test_result["success"]:
            logger.info(f"✅ {test_name} - PASS ({result['response_time']:.2f}ms)")
        else:
            logger.error(
                f"❌ {test_name} - FAIL (Status: {result['status_code']}, Expected: {expected_status})"
            )
            if result.get("error"):
                logger.error(f"   Error: {result['error']}")


class GAP001_CrossSystemFailureTests(E2ETestFramework):
    """GAP-001: 跨系統失敗回補驗證測試"""

    def test_invalid_organ_number(self):
        """測試無效機構編號的處理"""
        test_data = {
            "organNo": "00000000",  # 無效編號
            "organ": "測試機構",
            "brief": "測試簡介",
            "mode": "OPTIMIZE",
        }

        result = self._make_request("POST", "/v1/company/profile/process", test_data)
        self._record_test_result("跨系統-無效機構編號測試", result, 400, "HIGH")

        return result

    def test_network_timeout_simulation(self):
        """模擬網路超時情況"""
        test_data = {
            "organNo": "69188618",
            "organ": "測試機構",
            "brief": "測試簡介",
            "mode": "OPTIMIZE",
        }

        result = self._make_request(
            "POST", "/v1/company/profile/process", test_data, timeout=1
        )
        self._record_test_result("跨系統-網路超時模擬", result, 408, "HIGH")

        return result

    def test_malformed_request_data(self):
        """測試格式錯誤的請求資料"""
        test_cases = [
            {
                "organNo": "",
                "organ": "測試",
                "brief": "簡介",
                "mode": "OPTIMIZE",
            },  # 空機構編號
            {
                "organNo": "123",
                "organ": "",
                "brief": "簡介",
                "mode": "OPTIMIZE",
            },  # 空機構名稱
            {
                "organNo": "123",
                "organ": "測試",
                "brief": "",
                "mode": "OPTIMIZE",
            },  # 空簡介
            {
                "organNo": "123",
                "organ": "測試",
                "brief": "簡介",
                "mode": "INVALID",
            },  # 無效模式
        ]

        results = []
        for i, test_data in enumerate(test_cases):
            result = self._make_request(
                "POST", "/v1/company/profile/process", test_data
            )
            self._record_test_result(f"跨系統-格式錯誤測試{i + 1}", result, 400, "HIGH")
            results.append(result)

        return results


class GAP002_ConcurrentAnomalyTests(E2ETestFramework):
    """GAP-002: 多異常併發時序測試"""

    def test_concurrent_requests(self, num_requests: int = 5):
        """測試併發請求處理"""
        test_data = {
            "organNo": "69188618",
            "organ": "併發測試機構",
            "brief": "併發測試簡介",
            "mode": "OPTIMIZE",
        }

        results = []

        def make_concurrent_request(request_id):
            data = test_data.copy()
            data["organ"] = f"併發測試機構{request_id}"
            return self._make_request("POST", "/v1/company/profile/process", data)

        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            future_to_id = {
                executor.submit(make_concurrent_request, i): i
                for i in range(num_requests)
            }

            for future in as_completed(future_to_id):
                request_id = future_to_id[future]
                try:
                    result = future.result()
                    self._record_test_result(
                        f"併發請求-{request_id}", result, 200, "HIGH"
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"併發請求 {request_id} 異常: {e}")

        return results

    def test_race_condition_simulation(self):
        """模擬競爭條件"""
        # 同時發送多個相同的請求
        test_data = {
            "organNo": "69188618",
            "organ": "競爭條件測試",
            "brief": "競爭條件測試簡介",
            "mode": "OPTIMIZE",
        }

        results = []

        def send_request():
            return self._make_request("POST", "/v1/company/profile/process", test_data)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_request) for _ in range(3)]

            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                self._record_test_result(f"競爭條件-{i + 1}", result, 200, "HIGH")
                results.append(result)

        return results


class GAP003_LogStreamingTests(E2ETestFramework):
    """GAP-003: 日誌串流異常斷點測試"""

    def test_log_search_functionality(self):
        """測試日誌搜尋功能"""
        # 首先產生一些請求以建立日誌
        test_data = {
            "organNo": "69188618",
            "organ": "日誌測試機構",
            "brief": "日誌測試簡介",
            "mode": "OPTIMIZE",
        }

        # 發送請求以產生日誌
        self._make_request("POST", "/v1/company/profile/process", test_data)

        # 稍等一下讓日誌寫入
        time.sleep(1)

        # 測試日誌查詢
        result = self._make_request(
            "GET", "/v1/monitoring/logs?level=INFO&page=1&page_size=10"
        )
        self._record_test_result("日誌搜尋功能測試", result, 200, "MEDIUM")

        return result

    def test_anomaly_monitoring(self):
        """測試異常監控功能"""
        result = self._make_request("GET", "/v1/monitoring/anomalies")
        self._record_test_result("異常監控功能測試", result, 200, "MEDIUM")

        return result

    def test_health_check(self):
        """測試健康檢查端點"""
        result = self._make_request("GET", "/health")
        self._record_test_result("健康檢查測試", result, 200, "LOW")

        return result


class GAP004_BatchHistoricalDataTests(E2ETestFramework):
    """GAP-004: 批次歷史數據覆蓋測試"""

    def test_large_brief_processing(self):
        """測試大型簡介處理"""
        # 建立長簡介
        long_brief = "這是一個非常長的機構簡介。" * 100  # 約2000字

        test_data = {
            "organNo": "69188618",
            "organ": "大型資料測試機構",
            "brief": long_brief,
            "mode": "OPTIMIZE",
        }

        result = self._make_request(
            "POST", "/v1/company/profile/process", test_data, timeout=60
        )
        self._record_test_result("大型簡介處理測試", result, 200, "MEDIUM")

        return result

    def test_batch_processing_simulation(self):
        """模擬批次處理"""
        batch_data = []
        for i in range(10):
            test_data = {
                "organNo": f"6918861{i}",
                "organ": f"批次測試機構{i}",
                "brief": f"批次測試簡介{i}，包含一些測試內容。",
                "mode": "OPTIMIZE",
            }
            batch_data.append(test_data)

        results = []
        start_time = time.time()

        for i, data in enumerate(batch_data):
            result = self._make_request("POST", "/v1/company/profile/process", data)
            self._record_test_result(f"批次處理-{i + 1}", result, 200, "MEDIUM")
            results.append(result)

        total_time = time.time() - start_time
        logger.info(f"批次處理完成，總時間: {total_time:.2f}秒")

        return results


class E2ETestRunner:
    """E2E 測試執行器"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_suites = [
            GAP001_CrossSystemFailureTests(base_url),
            GAP002_ConcurrentAnomalyTests(base_url),
            GAP003_LogStreamingTests(base_url),
            GAP004_BatchHistoricalDataTests(base_url),
        ]

    def run_all_tests(self) -> Dict[str, Any]:
        """執行所有測試"""
        logger.info("開始執行 E2E 測試補強腳本")
        start_time = time.time()

        all_results = []

        # GAP-001 測試
        logger.info("執行 GAP-001: 跨系統失敗回補驗證測試")
        gap001 = self.test_suites[0]
        gap001.test_invalid_organ_number()
        gap001.test_network_timeout_simulation()
        gap001.test_malformed_request_data()
        all_results.extend(gap001.test_results)

        # GAP-002 測試
        logger.info("執行 GAP-002: 多異常併發時序測試")
        gap002 = self.test_suites[1]
        gap002.test_concurrent_requests(3)
        gap002.test_race_condition_simulation()
        all_results.extend(gap002.test_results)

        # GAP-003 測試
        logger.info("執行 GAP-003: 日誌串流異常斷點測試")
        gap003 = self.test_suites[2]
        gap003.test_log_search_functionality()
        gap003.test_anomaly_monitoring()
        gap003.test_health_check()
        all_results.extend(gap003.test_results)

        # GAP-004 測試
        logger.info("執行 GAP-004: 批次歷史數據覆蓋測試")
        gap004 = self.test_suites[3]
        gap004.test_large_brief_processing()
        gap004.test_batch_processing_simulation()
        all_results.extend(gap004.test_results)

        # 統計結果
        total_time = time.time() - start_time
        total_tests = len(all_results)
        passed_tests = len([r for r in all_results if r["success"]])
        failed_tests = total_tests - passed_tests

        # 按嚴重度分組
        severity_stats = {}
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            severity_results = [r for r in all_results if r["severity"] == severity]
            severity_passed = len([r for r in severity_results if r["success"]])
            severity_total = len(severity_results)
            severity_stats[severity] = {
                "total": severity_total,
                "passed": severity_passed,
                "failed": severity_total - severity_passed,
            }

        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time": round(total_time, 2),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": round(passed_tests / total_tests * 100, 2)
            if total_tests > 0
            else 0,
            "severity_stats": severity_stats,
            "detailed_results": all_results,
        }

        logger.info(
            f"測試完成！總計 {total_tests} 個測試，通過 {passed_tests} 個，失敗 {failed_tests} 個"
        )
        logger.info(f"通過率: {summary['pass_rate']}%")

        return summary

    def save_test_report(
        self, summary: Dict[str, Any], filename: str = "e2e_test_report.json"
    ):
        """儲存測試報告"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"測試報告已儲存至: {filename}")


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="E2E 測試補強腳本")
    parser.add_argument("--url", default="http://localhost:5000", help="API 基礎 URL")
    parser.add_argument(
        "--output", default="e2e_test_report.json", help="輸出報告檔案名"
    )

    args = parser.parse_args()

    runner = E2ETestRunner(args.url)
    summary = runner.run_all_tests()
    runner.save_test_report(summary, args.output)


if __name__ == "__main__":
    main()
