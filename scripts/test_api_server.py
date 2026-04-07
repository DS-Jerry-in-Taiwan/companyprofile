#!/usr/bin/env python3
"""
測試專用API服務啟動器
在不同端口啟動包含新功能的API服務用於測試
"""

import sys
import os

# 設定路徑
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNCTIONS_DIR = os.path.join(PROJECT_ROOT, "src", "functions")
sys.path.insert(0, FUNCTIONS_DIR)

# 導入更新後的API控制器
from api_controller import app

if __name__ == "__main__":
    print("🚀 啟動測試版本API服務（端口 5001）")
    print("包含新功能：")
    print("  - /v1/company/profile/process (強化版)")
    print("  - /v1/monitoring/logs (日誌查詢)")
    print("  - /v1/monitoring/anomalies (異常統計)")
    print("  - /health (健康檢查)")

    try:
        app.run(debug=True, host="0.0.0.0", port=5001, use_reloader=False)
    except KeyboardInterrupt:
        print("\n✅ API服務已停止")
