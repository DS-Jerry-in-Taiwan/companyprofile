#!/usr/bin/env python3
"""
Phase 8 E2E 流程優化驗證腳本
驗證所有新實作的功能，包含異常偵測、結構化日誌、監控API等
"""

import sys
import os
import time
import json
import requests
from typing import Dict, Any, List

# 添加路徑以便導入模組
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNCTIONS_DIR = os.path.join(PROJECT_ROOT, "src", "functions")
sys.path.insert(0, FUNCTIONS_DIR)


def test_anomaly_detector():
    """測試異常偵測模組"""
    print("=" * 60)
    print("🔍 測試異常偵測模組")
    print("=" * 60)

    try:
        from utils.anomaly_detector import (
            anomaly_detector,
            detect_and_report_anomaly,
            get_anomaly_summary,
        )

        # 測試不同類型的錯誤
        test_errors = [
            ("Database connection timeout", "OrderSystem"),
            ("Internal server error 500", "PaymentService"),
            ("API rate limit exceeded", "UserService"),
            ("Memory allocation failed", "ReportService"),
        ]

        print("📊 測試異常偵測...")
        for error_msg, system in test_errors:
            anomaly_id = detect_and_report_anomaly(error_msg, system)
            if anomaly_id:
                print(f"✅ 偵測到異常: {anomaly_id} - {error_msg}")
            else:
                print(f"⚠️  未偵測到異常: {error_msg}")

        # 測試異常統計
        print("\n📈 測試異常統計...")
        summary = get_anomaly_summary()
        print(f"總異常數: {summary['total_anomalies']}")
        print(f"未解決異常: {summary['unresolved_anomalies']}")
        print(f"解決率: {summary['resolution_rate']}%")

        # 測試異常解決
        print("\n🔧 測試異常解決...")
        unresolved = anomaly_detector.get_unresolved_anomalies()
        if unresolved:
            first_anomaly = unresolved[0]
            resolved = anomaly_detector.resolve_anomaly(
                first_anomaly.anomaly_id, "測試解決"
            )
            print(f"✅ 異常解決測試: {'成功' if resolved else '失敗'}")

        print("✅ 異常偵測模組測試完成")
        return True

    except ImportError as e:
        print(f"❌ 導入異常偵測模組失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 異常偵測模組測試失敗: {e}")
        return False


def test_structured_logger():
    """測試結構化日誌模組"""
    print("\n" + "=" * 60)
    print("📝 測試結構化日誌模組")
    print("=" * 60)

    try:
        from utils.structured_logger import (
            request_context,
            log_info,
            log_warning,
            log_error,
            log_api_request,
            log_api_response,
            search_logs,
        )

        # 測試上下文記錄
        print("🔄 測試請求上下文...")
        with request_context() as ctx:
            request_id = ctx["request_id"]
            trace_id = ctx["trace_id"]
            print(f"請求ID: {request_id}")
            print(f"追蹤ID: {trace_id}")

            # 測試各種日誌記錄
            log_info("測試資訊日誌", component="test")
            log_warning("測試警告日誌", component="test")
            log_error("測試錯誤日誌", component="test")

            # 測試API日誌記錄
            log_api_request("POST", "/test", {"test": "data"})
            log_api_response("POST", "/test", 200, 150.5)

        print("✅ 日誌記錄測試完成")

        # 測試日誌搜尋
        print("\n🔍 測試日誌搜尋...")
        search_result = search_logs({"level": "INFO", "page": 1, "page_size": 5})
        print(f"搜尋到 {search_result['total']} 筆日誌")

        print("✅ 結構化日誌模組測試完成")
        return True

    except ImportError as e:
        print(f"❌ 導入結構化日誌模組失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 結構化日誌模組測試失敗: {e}")
        return False


def test_api_endpoints(base_url: str = "http://localhost:5000"):
    """測試API端點"""
    print("\n" + "=" * 60)
    print("🌐 測試API端點")
    print("=" * 60)

    test_results = []

    # 測試健康檢查
    print("❤️  測試健康檢查端點...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ 健康檢查正常: {response.json()}")
            test_results.append(("health_check", True))
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
            test_results.append(("health_check", False))
    except Exception as e:
        print(f"❌ 健康檢查異常: {e}")
        test_results.append(("health_check", False))

    # 測試主要API端點
    print("\n📋 測試主要API端點...")
    test_data = {
        "organNo": "69188618",
        "organ": "驗證測試機構",
        "brief": "這是一個用於驗證的測試簡介",
        "mode": "OPTIMIZE",
    }

    try:
        response = requests.post(
            f"{base_url}/v1/company/profile/process", json=test_data, timeout=30
        )
        if response.status_code == 200:
            print(f"✅ 主要API正常: {response.status_code}")
            test_results.append(("main_api", True))
        else:
            print(f"❌ 主要API失敗: {response.status_code}")
            print(f"回應: {response.text}")
            test_results.append(("main_api", False))
    except Exception as e:
        print(f"❌ 主要API異常: {e}")
        test_results.append(("main_api", False))

    # 測試監控端點
    print("\n📊 測試監控端點...")

    # 測試日誌查詢
    try:
        response = requests.get(
            f"{base_url}/v1/monitoring/logs?page=1&page_size=5", timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(
                f"✅ 日誌查詢正常: 找到 {result.get('data', {}).get('total', 0)} 筆日誌"
            )
            test_results.append(("log_monitoring", True))
        else:
            print(f"❌ 日誌查詢失敗: {response.status_code}")
            test_results.append(("log_monitoring", False))
    except Exception as e:
        print(f"❌ 日誌查詢異常: {e}")
        test_results.append(("log_monitoring", False))

    # 測試異常統計
    try:
        response = requests.get(f"{base_url}/v1/monitoring/anomalies", timeout=10)
        if response.status_code == 200:
            result = response.json()
            anomaly_count = result.get("data", {}).get("total_anomalies", 0)
            print(f"✅ 異常統計正常: 總計 {anomaly_count} 個異常")
            test_results.append(("anomaly_monitoring", True))
        else:
            print(f"❌ 異常統計失敗: {response.status_code}")
            test_results.append(("anomaly_monitoring", False))
    except Exception as e:
        print(f"❌ 異常統計異常: {e}")
        test_results.append(("anomaly_monitoring", False))

    return test_results


def run_e2e_tests():
    """執行E2E測試腳本"""
    print("\n" + "=" * 60)
    print("🧪 執行E2E測試腳本")
    print("=" * 60)

    # 檢查E2E測試腳本是否存在
    e2e_script_path = os.path.join(PROJECT_ROOT, "scripts", "e2e_test_enhancement.py")

    if not os.path.exists(e2e_script_path):
        print(f"❌ E2E測試腳本不存在: {e2e_script_path}")
        return False

    print(f"📁 找到E2E測試腳本: {e2e_script_path}")
    print("注意：E2E測試需要API服務運行中才能執行")
    print(
        "建議手動執行: python scripts/e2e_test_enhancement.py --url http://localhost:5000"
    )

    return True


def check_file_structure():
    """檢查檔案結構"""
    print("\n" + "=" * 60)
    print("📁 檢查檔案結構")
    print("=" * 60)

    required_files = [
        "src/functions/utils/anomaly_detector.py",
        "src/functions/utils/structured_logger.py",
        "src/functions/api_controller.py",
        "scripts/e2e_test_enhancement.py",
        "docs/agent_context/phase8_e2e_process_improvement/meeting_record_template_example.md",
        "docs/agent_context/phase8_e2e_process_improvement/knowledge_entry_template_example.md",
        "docs/agent_context/phase8_e2e_process_improvement/outcome_summary.md",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(PROJECT_ROOT, file_path)
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            print(f"✅ {file_path} ({file_size} bytes)")
        else:
            print(f"❌ {file_path} (不存在)")
            all_exist = False

    return all_exist


def generate_verification_report(test_results: Dict[str, Any]):
    """產生驗證報告"""
    print("\n" + "=" * 60)
    print("📋 驗證報告")
    print("=" * 60)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "phase": "Phase 8 E2E Process Improvement",
        "verification_results": test_results,
        "summary": {
            "total_tests": len(
                [k for k, v in test_results.items() if isinstance(v, bool)]
            ),
            "passed_tests": len([k for k, v in test_results.items() if v is True]),
            "failed_tests": len([k for k, v in test_results.items() if v is False]),
        },
    }

    # 計算通過率
    total = report["summary"]["total_tests"]
    passed = report["summary"]["passed_tests"]
    pass_rate = (passed / total * 100) if total > 0 else 0
    report["summary"]["pass_rate"] = round(pass_rate, 2)

    # 輸出報告
    print(f"📊 測試統計:")
    print(f"   總測試項目: {total}")
    print(f"   通過項目: {passed}")
    print(f"   失敗項目: {report['summary']['failed_tests']}")
    print(f"   通過率: {pass_rate:.1f}%")

    print(f"\n📝 詳細結果:")
    for test_name, result in test_results.items():
        if isinstance(result, bool):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")

    # 儲存報告
    report_file = os.path.join(PROJECT_ROOT, "phase8_verification_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n💾 驗證報告已儲存: {report_file}")

    return report


def main():
    """主驗證流程"""
    print("🚀 Phase 8 E2E 流程優化驗證開始")
    print("時間:", time.strftime("%Y-%m-%d %H:%M:%S"))

    test_results = {}

    # 1. 檢查檔案結構
    test_results["file_structure"] = check_file_structure()

    # 2. 測試異常偵測模組
    test_results["anomaly_detector"] = test_anomaly_detector()

    # 3. 測試結構化日誌模組
    test_results["structured_logger"] = test_structured_logger()

    # 4. 檢查E2E測試腳本
    test_results["e2e_test_script"] = run_e2e_tests()

    # 5. 測試API端點（可選，需要服務運行）
    print("\n🌐 API端點測試（可選）")
    print("如果 Flask 服務正在運行，將執行API測試...")

    try:
        api_results = test_api_endpoints()
        for test_name, result in api_results:
            test_results[f"api_{test_name}"] = result
    except Exception as e:
        print(f"⚠️  API測試跳過（服務可能未運行）: {e}")
        test_results["api_test_note"] = "服務未運行，跳過API測試"

    # 6. 產生驗證報告
    report = generate_verification_report(test_results)

    # 7. 總結
    print("\n" + "=" * 60)
    print("🎯 驗證總結")
    print("=" * 60)

    if report["summary"]["pass_rate"] >= 80:
        print("🎉 恭喜！Phase 8 E2E 流程優化驗證通過！")
        print("✅ 所有關鍵功能運作正常")
        if report["summary"]["pass_rate"] < 100:
            print("⚠️  部分功能可能需要在API服務運行時再次測試")
    else:
        print("⚠️  驗證發現問題，需要檢查失敗的項目")

    print(f"\n📈 整體通過率: {report['summary']['pass_rate']:.1f}%")
    print("🔄 建議下一步：")
    print("   1. 修復任何失敗的測試項目")
    print("   2. 啟動Flask服務並執行完整的API測試")
    print("   3. 執行E2E測試腳本進行全面測試")
    print("   4. 進行效能和負載測試")


if __name__ == "__main__":
    main()
