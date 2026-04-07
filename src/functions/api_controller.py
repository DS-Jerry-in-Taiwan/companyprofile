# api_controller.py
"""
API Gateway / Controller
- Flask 實作，單一端點 POST /v1/company/profile/process
- 整合結構化日誌和異常偵測
"""

import time
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.request_validator import validate_request, ValidationError
from utils.core_dispatcher import dispatch_core_logic
from utils.error_handler import ExternalServiceError, LLMServiceError
from utils.response_formatter import (
    build_success_response,
    build_error_response,
    build_server_error_response,
)
from utils.structured_logger import (
    request_context,
    log_api_request,
    log_api_response,
    log_error,
    log_warning,
    log_info,
    get_current_request_id,
    search_logs,
)
from utils.anomaly_detector import detect_and_report_anomaly, get_anomaly_summary

app = Flask(__name__)
CORS(app)


@app.route("/v1/company/profile/process", methods=["POST"])
def process_company_profile():
    start_time = time.time()

    with request_context() as ctx:
        request_id = ctx["request_id"]
        trace_id = ctx["trace_id"]

        try:
            # 記錄 API 請求
            data = request.get_json(force=True)
            log_api_request(
                method="POST",
                path="/v1/company/profile/process",
                request_data={"organNo": data.get("organNo"), "mode": data.get("mode")},
                component="api_gateway",
            )

            # 驗證請求
            log_info("開始請求驗證", component="validation")
            valid_data = validate_request(data)
            log_info("請求驗證成功", component="validation")

            # 執行核心邏輯
            log_info("開始執行核心邏輯", component="core_logic")
            result = dispatch_core_logic(valid_data)
            log_info("核心邏輯執行完成", component="core_logic")

            # 記錄成功回應
            response_time_ms = (time.time() - start_time) * 1000
            response_data = build_success_response(valid_data, result)

            log_api_response(
                method="POST",
                path="/v1/company/profile/process",
                status_code=200,
                response_time_ms=response_time_ms,
                response_data={"status": "success", "data_size": len(str(result))},
                component="api_gateway",
            )

            return jsonify(response_data)

        except ValidationError as ve:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"驗證錯誤: {ve.message}"

            # 記錄警告並偵測異常
            log_warning(
                error_msg,
                component="validation",
                error_code=ve.code,
                error_details=ve.details,
            )

            anomaly_id = detect_and_report_anomaly(
                error_msg, "OrganBriefOptimization", trace_id
            )

            response_data = build_error_response(ve.code, ve.message, ve.details)

            log_api_response(
                method="POST",
                path="/v1/company/profile/process",
                status_code=400,
                response_time_ms=response_time_ms,
                response_data={"status": "error", "error_code": ve.code},
                component="api_gateway",
                anomaly_id=anomaly_id,
            )

            return jsonify(response_data), 400

        except (ExternalServiceError, LLMServiceError) as se:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"服務錯誤: {se.message}"

            # 記錄錯誤並偵測異常
            log_error(error_msg, exception=se, component="external_service")

            anomaly_id = detect_and_report_anomaly(
                error_msg, "OrganBriefOptimization", trace_id
            )

            response_data = build_server_error_response(
                se.message, request_id=request_id
            )

            log_api_response(
                method="POST",
                path="/v1/company/profile/process",
                status_code=500,
                response_time_ms=response_time_ms,
                response_data={"status": "error", "request_id": request_id},
                component="api_gateway",
                anomaly_id=anomaly_id,
            )

            return jsonify(response_data), 500

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"未預期的錯誤: {type(e).__name__}: {str(e)}"

            # 記錄嚴重錯誤並偵測異常
            log_error(error_msg, exception=e, component="api_gateway")

            anomaly_id = detect_and_report_anomaly(
                error_msg, "OrganBriefOptimization", trace_id
            )

            response_data = build_server_error_response(str(e), request_id=request_id)

            log_api_response(
                method="POST",
                path="/v1/company/profile/process",
                status_code=500,
                response_time_ms=response_time_ms,
                response_data={"status": "error", "request_id": request_id},
                component="api_gateway",
                anomaly_id=anomaly_id,
            )

            return jsonify(response_data), 500


@app.route("/v1/monitoring/logs", methods=["GET"])
def get_logs():
    """日誌查詢端點"""
    with request_context() as ctx:
        try:
            # 取得查詢參數
            query = {}

            if request.args.get("trace_id"):
                query["trace_id"] = request.args.get("trace_id")
            if request.args.get("request_id"):
                query["request_id"] = request.args.get("request_id")
            if request.args.get("level"):
                query["level"] = request.args.get("level")
            if request.args.get("start_time"):
                query["start_time"] = request.args.get("start_time")
            if request.args.get("end_time"):
                query["end_time"] = request.args.get("end_time")
            if request.args.get("keyword"):
                query["keyword"] = request.args.get("keyword")
            if request.args.get("page"):
                query["page"] = int(request.args.get("page"))
            if request.args.get("page_size"):
                query["page_size"] = int(request.args.get("page_size"))

            log_info("日誌查詢請求", component="monitoring", query_params=query)

            # 執行搜尋
            result = search_logs(query)

            log_info(
                "日誌查詢完成", component="monitoring", result_count=result["total"]
            )

            return jsonify({"status": "success", "data": result})

        except Exception as e:
            log_error("日誌查詢失敗", exception=e, component="monitoring")
            return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/v1/monitoring/anomalies", methods=["GET"])
def get_anomalies():
    """異常統計端點"""
    with request_context() as ctx:
        try:
            log_info("異常統計請求", component="monitoring")

            summary = get_anomaly_summary()

            log_info(
                "異常統計完成",
                component="monitoring",
                total_anomalies=summary["total_anomalies"],
            )

            return jsonify({"status": "success", "data": summary})

        except Exception as e:
            log_error("異常統計失敗", exception=e, component="monitoring")
            return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """健康檢查端點"""
    with request_context() as ctx:
        log_info("健康檢查", component="health_check")
        return jsonify(
            {
                "status": "healthy",
                "timestamp": time.time(),
                "request_id": get_current_request_id(),
            }
        )


@app.route("/config", methods=["GET"])
def get_config():
    return jsonify({"apiBaseUrl": "/api/v1", "version": "1.0.0"})


if __name__ == "__main__":
    app.run(debug=True)
