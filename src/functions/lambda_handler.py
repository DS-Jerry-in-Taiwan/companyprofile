# lambda_handler.py
"""
AWS Lambda 入口點 - 手動 WSGI 適配器
將 Flask WSGI 應用程式包裝為 Lambda 相容的處理函數

支援:
- API Gateway HTTP API v2 (既有)
- ALB (新增)
Version: 2.0
"""

import base64
import io
import json
import os
from urllib.parse import urlencode
from api_controller import app


# ===== ALB Path Prefix 配置 =====
# 依 stage 決定 prefix，與 ALB rule path pattern 一致
ALB_PATH_PREFIXES = {
    "dev": "/organ-brief-dev/api/recurit/optimize",
    "prod": "/organ-brief-prd/api/recurit/optimize",
}

_current_stage = os.environ.get("STAGE", "dev")
ALB_PATH_PREFIX = ALB_PATH_PREFIXES.get(_current_stage, "")


def _strip_alb_prefix(path: str) -> str:
    """移除 ALB path prefix，讓 Flask 看到原始路由"""
    if ALB_PATH_PREFIX and path.startswith(ALB_PATH_PREFIX):
        stripped = path[len(ALB_PATH_PREFIX):]
        return stripped or "/"
    return path


# ===== Event 來源偵測 =====

def _is_alb_event(event: dict) -> bool:
    """判斷 event 是否來自 ALB (有 requestContext.elb)"""
    return bool(event.get("requestContext", {}).get("elb"))


# ===== ALB Event 解析 =====

def _build_query_string(params: dict) -> str:
    """將 dict 轉為 query string (key=value&key2=value2)"""
    if not params:
        return ""
    return urlencode(params)


def _decode_body(body, is_base64: bool) -> bytes:
    """解碼 body (base64 或純文字)"""
    if not body:
        return b""
    if is_base64:
        return base64.b64decode(body)
    if isinstance(body, str):
        return body.encode("utf-8")
    return body


def _parse_alb_event(event: dict) -> dict:
    """解析 ALB event → WSGI environ 所需的欄位"""
    return {
        "http_method": event.get("httpMethod", "GET"),
        "path": event.get("path", "/"),
        "query_string": _build_query_string(event.get("queryStringParameters", {})),
        "headers": event.get("headers", {}),
        "body": _decode_body(event.get("body", ""), event.get("isBase64Encoded", False)),
    }


# ===== API Gateway v2 Event 解析 (既有) =====

def _parse_apigwv2_event(event: dict) -> dict:
    """解析 API Gateway HTTP API v2 event → WSGI environ 所需的欄位"""
    body = event.get("body", "")
    is_base64 = event.get("isBase64Encoded", False)

    return {
        "http_method": event.get("requestContext", {}).get("http", {}).get("method", "GET"),
        "path": event.get("rawPath", "/"),
        "query_string": event.get("rawQueryString", ""),
        "headers": event.get("headers", {}),
        "body": _decode_body(body, is_base64),
    }


# ===== WSGI 建構 =====

def _build_wsgi_environ(parsed: dict, alb_response: dict, is_alb: bool = False) -> tuple:
    """從 parsed event 建立 WSGI environ + 更新 alb_response"""
    http_method = parsed["http_method"]
    path = parsed["path"]
    query_string = parsed["query_string"]
    headers = parsed["headers"]
    body = parsed["body"]

    # 若是 ALB event，移除 path prefix
    if is_alb:
        path = _strip_alb_prefix(path)

    environ = {
        "REQUEST_METHOD": http_method,
        "SCRIPT_NAME": "",
        "PATH_INFO": path,
        "QUERY_STRING": query_string,
        "SERVER_NAME": headers.get("host", "lambda"),
        "SERVER_PORT": "443",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "https",
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": io.BytesIO(),
        "wsgi.multiprocess": False,
        "wsgi.multithread": False,
        "wsgi.run_once": False,
        "CONTENT_LENGTH": str(len(body)),
    }

    # 添加 HTTP headers 到環境
    for key, value in headers.items():
        key = key.upper().replace("-", "_")
        if key in ["CONTENT_TYPE", "CONTENT_LENGTH"]:
            environ[key] = value
        else:
            environ[f"HTTP_{key}"] = value

    return environ


# ===== 回應建構 =====

def _build_response(parsed: dict, response_data: dict) -> dict:
    """包裝 WSGI response 為 Lambda 回傳格式"""
    # ALB 需要 statusDescription
    status_code = response_data["statusCode"]
    status_text = {200: "OK", 201: "Created", 400: "Bad Request",
                   404: "Not Found", 500: "Internal Server Error"}
    response_data["statusDescription"] = f"{status_code} {status_text.get(status_code, 'Unknown')}"

    return response_data


# ===== Handler =====

def handler(event, context):
    """
    Lambda 處理函數
    自動偵測事件來源 (ALB / API Gateway v2) 並轉換為 WSGI 環境
    """
    # 調試：打印事件
    print(f"[DEBUG] Received event: {json.dumps(event)}")

    # 依來源選擇解析器，並記錄是否為 ALB event
    is_alb = _is_alb_event(event)
    if is_alb:
        print(f"[DEBUG] Detected ALB event")
        parsed = _parse_alb_event(event)
    else:
        print(f"[DEBUG] Detected API Gateway v2 event")
        parsed = _parse_apigwv2_event(event)

    print(f"[DEBUG] HTTP Method: {parsed['http_method']}, Path: {parsed['path']}")

    # 建構 WSGI 環境
    response_data = {"statusCode": 200, "headers": {}, "body": ""}

    def start_response(status, response_headers, exc_info=None):
        response_data["statusCode"] = int(status.split(" ")[0])
        for header, value in response_headers:
            response_data["headers"][header] = value

    environ = _build_wsgi_environ(parsed, response_data, is_alb=is_alb)

    # 調用 WSGI app
    response = app(environ, start_response)
    response_data["body"] = b"".join(response).decode("utf-8")

    # 包裝回應 (補上 ALB 需要的欄位)
    result = _build_response(parsed, response_data)

    return result
