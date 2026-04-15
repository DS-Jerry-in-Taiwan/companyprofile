#!/usr/bin/env python3
"""
簡單的 Flask 啟動腳本
"""

import os
import sys
import subprocess

# 切換到正確的目錄
os.chdir("/home/ubuntu/projects/OrganBriefOptimization/src/functions")

# 設置環境變數
env = os.environ.copy()
env["PYTHONPATH"] = (
    "/home/ubuntu/projects/OrganBriefOptimization/src/functions:"
    + env.get("PYTHONPATH", "")
)

# 啟動 Flask
print("啟動 Flask 應用...")
print(f"工作目錄: {os.getcwd()}")
print(f"Python 路徑: {sys.executable}")

# 使用 subprocess 啟動，這樣可以保持運行
cmd = [sys.executable, "api_controller.py"]
process = subprocess.Popen(
    cmd,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    universal_newlines=True,
)

print(f"Flask 進程已啟動，PID: {process.pid}")

# 讀取輸出
try:
    for line in process.stdout:
        print(f"[Flask] {line}", end="")
except KeyboardInterrupt:
    print("\n收到中斷信號，停止 Flask...")
    process.terminate()
    process.wait()
    print("Flask 已停止")
