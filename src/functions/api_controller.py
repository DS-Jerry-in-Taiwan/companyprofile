# api_controller.py
"""
API Gateway / Controller
- Flask 實作，單一端點 POST /v1/company/profile/process
- 整合結構化日誌和異常偵測
"""

import time
import traceback
import logging
import contextlib
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# 統一設定 root logger（只設一次，避免重複）
_root_logger = logging.getLogger()
_root_logger.setLevel(logging.INFO)
if not _root_logger.handlers:
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    _handler = logging.StreamHandler()
    _handler.setFormatter(formatter)
    _root_logger.addHandler(_handler)

# 禁用 werkzeug
log = logging.getLogger("werkzeug")
log.setLevel(logging.WARNING)

# 敏感欄位遮蔽
SENSITIVE_FIELDS = {"organNo", "password", "token", "secret", "api_key", "key"}

def _mask_sensitive(data: dict) -> dict:
    if not data:
        return {}
    return {k: "***" if k in SENSITIVE_FIELDS else v for k, v in data.items()}

# 必須在 import 之前定義 app
app = Flask(__name__)
CORS(app)

# 計時工具
timing_logger = logging.getLogger(__name__)

from utils.request_validator import validate_request, ValidationError
from utils.core_dispatcher import dispatch_core_logic
from utils.error_handler import (
    ExternalServiceError,
    LLMServiceError,
    ErrorResponse,
    ErrorDetail,
)
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

# 計時工具
timing_logger = logging.getLogger(__name__)

# 新增錯誤記錄功能
from utils.error_logger import ErrorLogger

# 全域 ErrorLogger 實例
_error_logger = None

def _get_error_logger():
    """取得 ErrorLogger 實例"""
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger()
    return _error_logger

def _save_error_to_db(trace_id, organ_no, organ_name, error_code, error_message, error_phase,
                     recoverable, request_payload, mode, optimization_mode):
    """記錄錯誤到 DB"""
    try:
        logger = _get_error_logger()
        logger.save_error(
            trace_id=trace_id,
            organ_no=organ_no,
            organ_name=organ_name,
            error_code=error_code,
            error_message=error_message,
            error_phase=error_phase,
            recoverable=recoverable,
            request_payload=request_payload,
            mode=mode,
            optimization_mode=optimization_mode,
        )
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to save error to DB: {e}")

def _save_failed_request_to_llm_responses(trace_id, organ_no, organ_name, error_code, request_payload, mode, optimization_mode):
    """記錄失敗請求到 llm_responses 表"""
    try:
        from datetime import datetime
        from src.storage.factory import StorageFactory
        import json
        
        storage = StorageFactory.create({"type": "sqlite", "connection": "sqlite:///data/llm_responses.db"})
        
        item = {
            "trace_id": trace_id,
            "status": "error",
            "error_code": error_code,
            "organ_no": organ_no,
            "organ_name": organ_name,
            "mode": mode,
            "optimization_mode": optimization_mode,
            "user_input": json.dumps(request_payload) if request_payload else None,
            "created_at": datetime.now().isoformat(),
        }
        
        storage.save_response(item)
        logging.getLogger(__name__).info(f"Saved failed request to llm_responses: trace_id={trace_id}, status=error")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to save failed request to llm_responses: {e}")


@contextlib.contextmanager
def measure(operation_name: str):
    """計時上下文管理器"""
    start = time.time()
    timing_logger.info(f"[TIMING] {operation_name} 開始")
    try:
        yield
    finally:
        elapsed = (time.time() - start) * 1000
        timing_logger.info(f"[TIMING] {operation_name} 完成，耗時 {elapsed:.2f}ms")


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
            with measure("整體請求處理"):
                result = dispatch_core_logic(valid_data)
            log_info("核心邏輯執行完成", component="core_logic")

            # 記錄成功回應
            response_time_ms = (time.time() - start_time) * 1000
            response_data = build_success_response(valid_data, result, trace_id)

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

            # 記錄客戶端輸入錯誤（level: INFO，不是 WARNING）
            log_info(
                ve.message,
                component="validation",
                error_code=ve.code,
                error_details=ve.details,
            )

            # 記錄錯誤到 DB（如果可用）
            _save_error_to_db(
                trace_id=trace_id,
                organ_no=data.get("organNo"),
                organ_name=data.get("organ"),
                error_code=ve.code,
                error_message=ve.message,
                error_phase="validation",
                recoverable=1,  # ValidationError 通常可復原
                request_payload=data,
                mode=data.get("mode"),
                optimization_mode=data.get("optimization_mode"),
            )

            # 記錄失敗到 llm_responses 表（單表設計）
            _save_failed_request_to_llm_responses(
                trace_id=trace_id,
                organ_no=data.get("organNo"),
                organ_name=data.get("organ"),
                error_code=ve.code,
                request_payload=data,
                mode=data.get("mode"),
                optimization_mode=data.get("optimization_mode"),
            )

            anomaly_id = detect_and_report_anomaly(
                ve.message, "OrganBriefOptimization", trace_id
            )

            error_response = ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=ve.code,
                    message=ve.message,
                    details=str(ve.details) if ve.details else None,
                    trace_id=trace_id,
                )
            )
            response_data = error_response.to_dict()

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

            # 記錄錯誤到 DB
            _save_error_to_db(
                trace_id=trace_id,
                organ_no=data.get("organNo"),
                organ_name=data.get("organ"),
                error_code=se.code,
                error_message=se.message,
                error_phase="external_service",
                recoverable=getattr(se, 'recoverable', 1),
                request_payload=data,
                mode=data.get("mode"),
                optimization_mode=data.get("optimization_mode"),
            )

            # 記錄失敗到 llm_responses 表（單表設計）
            _save_failed_request_to_llm_responses(
                trace_id=trace_id,
                organ_no=data.get("organNo"),
                organ_name=data.get("organ"),
                error_code=se.code,
                request_payload=data,
                mode=data.get("mode"),
                optimization_mode=data.get("optimization_mode"),
            )

            anomaly_id = detect_and_report_anomaly(
                error_msg, "OrganBriefOptimization", trace_id
            )

            # 使用例外原有的錯誤碼，而非 hardcoded "INTERNAL_SERVER_ERROR"
            error_response = ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=se.code,
                    message=se.message,
                    recoverable=getattr(se, 'recoverable', True),
                    trace_id=trace_id,
                )
            )
            response_data = error_response.to_dict()

            log_api_response(
                method="POST",
                path="/v1/company/profile/process",
                status_code=500,
                response_time_ms=response_time_ms,
                response_data={"status": "error", "error_code": se.code},
                component="api_gateway",
                anomaly_id=anomaly_id,
            )

            return jsonify(response_data), 500

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"未預期的錯誤: {type(e).__name__}: {str(e)}"

            from utils.error_handler import ErrorCode

            # 記錄嚴重錯誤並偵測異常
            log_error(error_msg, exception=e, component="api_gateway")

            # 記錄錯誤到 DB
            _save_error_to_db(
                trace_id=trace_id,
                organ_no=data.get("organNo"),
                organ_name=data.get("organ"),
                error_code=ErrorCode.API_009.code,
                error_message=str(e),
                error_phase="api_gateway",
                recoverable=0,
                request_payload=data,
                mode=data.get("mode"),
                optimization_mode=data.get("optimization_mode"),
            )

            # 記錄失敗到 llm_responses 表（單表設計）
            _save_failed_request_to_llm_responses(
                trace_id=trace_id,
                organ_no=data.get("organNo"),
                organ_name=data.get("organ"),
                error_code=ErrorCode.API_009.code,
                request_payload=data,
                mode=data.get("mode"),
                optimization_mode=data.get("optimization_mode"),
            )

            anomaly_id = detect_and_report_anomaly(
                error_msg, "OrganBriefOptimization", trace_id
            )

            # 使用 ErrorResponse schema 與標準錯誤代碼
            error_response = ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.API_009.code,
                    message=str(e),
                    trace_id=trace_id,
                )
            )
            response_data = error_response.to_dict()

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
    try:
        with request_context() as ctx:
            log_info("健康檢查", component="health_check")
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "request_id": get_current_request_id(),
                }
            )
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time(),
        }), 500


@app.route("/config", methods=["GET"])
def get_config():
    return jsonify({"apiBaseUrl": "/api/v1", "version": "1.0.0"})


@app.route("/version", methods=["GET"])
def get_version():
    """版本資訊端點"""
    import os

    return jsonify(
        {
            "version": os.environ.get("VERSION", "unknown"),
            "build_date": os.environ.get("BUILD_DATE", "unknown"),
            "stage": os.environ.get("STAGE", "unknown"),
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
