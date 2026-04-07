# lambda_handler.py
"""
AWS Lambda 入口點 - 手動 WSGI 適配器
將 Flask WSGI 應用程式包裝為 Lambda 相容的處理函數
Version: 1.1
"""

import base64
import io
import json
from urllib.parse import urlencode
from api_controller import app


def handler(event, context):
    """
    Lambda 處理函數
    手動將 API Gateway HTTP API 事件轉換為 WSGI 環境
    """
    # 調試：打印事件
    print(f"[DEBUG] Received event: {json.dumps(event)}")

    # 解析 HTTP API Gateway v2 事件
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")

    print(f"[DEBUG] HTTP Method: {http_method}, Path: {path}")
    query_string = event.get("rawQueryString", "")
    headers = event.get("headers", {})
    body = event.get("body", "")
    is_base64 = event.get("isBase64Encoded", False)

    # 如果 body 是 base64 編碼，解碼它
    if is_base64 and body:
        body = base64.b64decode(body)
    elif body:
        body = body.encode("utf-8")
    else:
        body = b""

    # 建立 WSGI 環境
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

    # 捕獲回應
    response_data = {"statusCode": 200, "headers": {}, "body": ""}

    def start_response(status, response_headers, exc_info=None):
        response_data["statusCode"] = int(status.split(" ")[0])
        for header, value in response_headers:
            response_data["headers"][header] = value

    # 調用 WSGI app
    response = app(environ, start_response)
    response_data["body"] = b"".join(response).decode("utf-8")

    return response_data
