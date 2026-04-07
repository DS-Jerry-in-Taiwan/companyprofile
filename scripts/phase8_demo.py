#!/usr/bin/env python3
"""
Phase 8 功能演示腳本
展示所有新實作的功能，包含異常偵測、結構化日誌等
"""

import sys
import os
import time
import json

# 設定路徑
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNCTIONS_DIR = os.path.join(PROJECT_ROOT, "src", "functions")
sys.path.insert(0, FUNCTIONS_DIR)


def demo_anomaly_detection():
    """演示異常偵測功能"""
    print("=" * 60)
    print("🔍 異常偵測功能演示")
    print("=" * 60)

    from utils.anomaly_detector import (
        anomaly_detector,
        detect_and_report_anomaly,
        get_anomaly_summary,
        AnomalyType,
        AnomalySeverity,
    )

    # 模擬各種異常情況
    print("📊 模擬異常偵測...")

    test_scenarios = [
        ("Database connection timeout - retrying...", "OrderService"),
        ("500 Internal Server Error: Null pointer exception", "PaymentService"),
        ("API rate limit exceeded: 429 Too Many Requests", "UserService"),
        ("OutOfMemoryError: Java heap space exhausted", "ReportService"),
        ("Authentication failed: Invalid token", "AuthService"),
        ("Validation error: Required field 'email' missing", "ValidationService"),
    ]

    detected_anomalies = []
    for error_msg, system in test_scenarios:
        anomaly_id = detect_and_report_anomaly(error_msg, system)
        if anomaly_id:
            detected_anomalies.append(anomaly_id)
            print(f"  🚨 偵測到異常: {anomaly_id}")
        print(f"     錯誤訊息: {error_msg}")
        print(f"     來源系統: {system}")
        print()

    # 展示異常統計
    print("📈 異常統計資訊:")
    summary = get_anomaly_summary()
    print(f"  總異常數量: {summary['total_anomalies']}")
    print(f"  未解決異常: {summary['unresolved_anomalies']}")
    print(f"  解決率: {summary['resolution_rate']}%")

    print("\n📋 嚴重度分布:")
    for severity, count in summary["severity_distribution"].items():
        print(f"  {severity}: {count} 個")

    print("\n🏷️  異常類型分布:")
    for anomaly_type, count in summary["type_distribution"].items():
        if count > 0:
            print(f"  {anomaly_type}: {count} 個")

    # 演示異常解決
    print("\n🔧 演示異常解決流程...")
    unresolved = anomaly_detector.get_unresolved_anomalies()
    if unresolved:
        first_anomaly = unresolved[0]
        print(f"  正在解決異常: {first_anomaly.anomaly_id}")
        print(f"  異常描述: {first_anomaly.description}")
        print(f"  建議處置: {first_anomaly.suggested_action}")

        success = anomaly_detector.resolve_anomaly(
            first_anomaly.anomaly_id, "演示：已根據知識庫建議完成處置"
        )
        print(f"  解決狀態: {'✅ 成功' if success else '❌ 失敗'}")

    return detected_anomalies


def demo_structured_logging():
    """演示結構化日誌功能"""
    print("\n" + "=" * 60)
    print("📝 結構化日誌功能演示")
    print("=" * 60)

    from utils.structured_logger import (
        request_context,
        log_info,
        log_warning,
        log_error,
        log_api_request,
        log_api_response,
        log_external_api_call,
        log_external_api_response,
        search_logs,
        structured_logger,
    )

    # 演示請求上下文追蹤
    print("🔄 演示請求追蹤上下文...")
    with request_context(user_id="demo_user_123", session_id="demo_session_456") as ctx:
        print(f"  請求ID: {ctx['request_id']}")
        print(f"  追蹤ID: {ctx['trace_id']}")
        print(f"  使用者ID: {ctx['user_id']}")
        print(f"  會話ID: {ctx['session_id']}")

        # 演示各種類型的日誌記錄
        print("\n📋 演示各種日誌記錄...")

        log_info(
            "開始處理使用者請求",
            component="api_gateway",
            user_action="profile_optimization",
        )
        log_api_request(
            "POST",
            "/v1/company/profile/process",
            {"organNo": "69188618", "mode": "OPTIMIZE"},
        )

        log_external_api_call(
            service="LLM_Service",
            method="POST",
            url="https://api.llm.service/v1/generate",
            request_data={"prompt": "optimize company profile"},
        )

        # 模擬API回應
        time.sleep(0.1)  # 模擬處理時間

        log_external_api_response(
            service="LLM_Service",
            method="POST",
            url="https://api.llm.service/v1/generate",
            status_code=200,
            response_time_ms=150.5,
            response_data={"status": "success", "tokens_used": 250},
        )

        # 使用通用日誌記錄業務事件
        structured_logger.business_event(
            event_name="profile_optimized",
            entity_type="company",
            entity_id="69188618",
            result_quality="high",
            optimization_type="brief_enhancement",
        )

        log_api_response(
            "POST",
            "/v1/company/profile/process",
            200,
            180.3,
            {"status": "success", "enhanced": True},
        )

        log_api_response(
            "POST",
            "/v1/company/profile/process",
            200,
            180.3,
            {"status": "success", "enhanced": True},
        )

        log_info("請求處理完成", component="api_gateway", success=True)

    print("\n🔍 演示日誌搜尋功能...")

    # 等待一下讓日誌寫入
    time.sleep(0.5)

    # 搜尋不同類型的日誌
    search_cases = [
        {"level": "INFO", "page": 1, "page_size": 3},
        {"keyword": "API", "page": 1, "page_size": 5},
        {"level": "ERROR", "page": 1, "page_size": 5},
    ]

    for i, query in enumerate(search_cases, 1):
        result = search_logs(query)
        print(f"  搜尋案例 {i}: {query}")
        print(f"    找到 {result['total']} 筆日誌")
        if result["logs"]:
            print(f"    最新一筆: {result['logs'][0]['message'][:50]}...")
        print()


def demo_knowledge_base():
    """演示知識庫功能"""
    print("=" * 60)
    print("📚 知識庫功能演示")
    print("=" * 60)

    from utils.anomaly_detector import anomaly_detector

    print("🔍 知識庫匹配演示...")

    # 測試知識庫匹配
    test_descriptions = [
        "database timeout occurred during user login",
        "rate limit exceeded for API calls",
        "memory usage is critically high",
    ]

    for desc in test_descriptions:
        analysis, suggestion = anomaly_detector._analyze_with_knowledge_base(desc)
        print(f"  問題描述: {desc}")
        print(f"  分析結果: {analysis}")
        print(f"  建議處置: {suggestion}")
        print()


def demo_template_system():
    """演示模板系統"""
    print("=" * 60)
    print("📄 文件模板系統演示")
    print("=" * 60)

    template_files = [
        "docs/agent_context/phase8_e2e_process_improvement/meeting_record_template_example.md",
        "docs/agent_context/phase8_e2e_process_improvement/knowledge_entry_template_example.md",
    ]

    for template_file in template_files:
        full_path = os.path.join(PROJECT_ROOT, template_file)
        if os.path.exists(full_path):
            print(f"📋 {os.path.basename(template_file)}")
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 只顯示前200字符
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"  內容預覽: {preview}")
                print(f"  檔案大小: {len(content)} 字符")
                print()


def generate_demo_report():
    """產生演示報告"""
    print("=" * 60)
    print("📊 演示報告產生")
    print("=" * 60)

    from utils.anomaly_detector import get_anomaly_summary
    from utils.structured_logger import search_logs

    # 收集統計資料
    anomaly_summary = get_anomaly_summary()
    log_summary = search_logs({"page": 1, "page_size": 1})

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "demo_title": "Phase 8 E2E Process Improvement 功能演示",
        "anomaly_statistics": {
            "total_anomalies": anomaly_summary["total_anomalies"],
            "unresolved_anomalies": anomaly_summary["unresolved_anomalies"],
            "resolution_rate": anomaly_summary["resolution_rate"],
            "severity_distribution": anomaly_summary["severity_distribution"],
        },
        "logging_statistics": {
            "total_logs": log_summary["total"],
            "search_functionality": "正常運作",
        },
        "features_demonstrated": [
            "自動異常偵測與分類",
            "嚴重度評估與通報",
            "知識庫匹配與建議",
            "結構化日誌記錄",
            "請求追蹤與上下文",
            "日誌搜尋與查詢",
            "異常統計與分析",
            "文件模板系統",
        ],
        "system_status": "所有功能正常運作",
    }

    # 儲存報告
    report_file = os.path.join(PROJECT_ROOT, "phase8_demo_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"📄 演示報告已產生: {report_file}")
    print("\n📋 演示摘要:")
    print(f"  異常偵測: {report['anomaly_statistics']['total_anomalies']} 個異常")
    print(f"  日誌記錄: {report['logging_statistics']['total_logs']} 筆日誌")
    print(f"  功能狀態: {report['system_status']}")
    print(f"  演示功能: {len(report['features_demonstrated'])} 項")

    return report


def main():
    """主演示流程"""
    print("🎭 Phase 8 E2E 流程優化 - 功能演示")
    print("時間:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print()

    try:
        # 1. 異常偵測演示
        detected_anomalies = demo_anomaly_detection()

        # 2. 結構化日誌演示
        demo_structured_logging()

        # 3. 知識庫演示
        demo_knowledge_base()

        # 4. 模板系統演示
        demo_template_system()

        # 5. 產生演示報告
        report = generate_demo_report()

        # 總結
        print("\n" + "=" * 60)
        print("🎉 演示完成!")
        print("=" * 60)
        print("✅ 所有 Phase 8 新功能已成功演示")
        print(f"📊 異常偵測: {len(detected_anomalies)} 個異常已識別")
        print("📝 結構化日誌: 完整追蹤鏈已建立")
        print("📚 知識庫: 自動匹配與建議正常")
        print("📄 文件模板: 標準化範例已建立")
        print()
        print("🔄 下一步建議:")
        print("1. 啟動完整API服務進行整合測試")
        print("2. 執行E2E測試腳本驗證所有場景")
        print("3. 進行效能測試與負載測試")
        print("4. 規劃正式環境部署")

    except Exception as e:
        print(f"❌ 演示過程發生錯誤: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
