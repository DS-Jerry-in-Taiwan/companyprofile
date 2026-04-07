#!/usr/bin/env python3
"""
測試 WSGI 適配器的本地腳本
"""

import sys

sys.path.insert(0, "/home/ubuntu/projects/OrganBriefOptimization/src/functions")

from lambda_handler import handler

# 模擬 API Gateway 事件 - GET /health
event_health = {
    "version": "2.0",
    "routeKey": "GET /health",
    "rawPath": "/health",
    "rawQueryString": "",
    "headers": {"accept": "application/json", "host": "lambda.test"},
    "requestContext": {
        "http": {
            "method": "GET",
            "path": "/health",
            "protocol": "HTTP/1.1",
            "sourceIp": "127.0.0.1",
        }
    },
    "isBase64Encoded": False,
}


# 模擬 context
class Context:
    def __init__(self):
        self.request_id = "test-123"
        self.function_name = "test-function"


# 測試
print("=" * 60)
print("測試 GET /health")
print("=" * 60)
result = handler(event_health, Context())
print(f"Status Code: {result['statusCode']}")
print(f"Headers: {result['headers']}")
print(f"Body: {result['body']}")
