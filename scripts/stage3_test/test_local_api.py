#!/usr/bin/env python3
"""
本地 API 效能測試
"""

import requests
import time
import json

API_URL = "http://localhost:5000"
COMPANY = "私立揚才文理短期補習班"
ITERATIONS = 3


def test_api(model_name=""):
    """測試 API"""
    print(f"==========================================")
    print(f"測試: {model_name}")
    print(f"==========================================")
    print()

    times = []

    for i in range(1, ITERATIONS + 1):
        print(f"第 {i}/{ITERATIONS} 次測試...")

        payload = {"organNo": "1", "organ": COMPANY, "mode": "GENERATE"}

        start = time.time()

        try:
            response = requests.post(
                f"{API_URL}/v1/company/profile/process", json=payload, timeout=60
            )

            end = time.time()
            elapsed_ms = (end - start) * 1000

            try:
                data = response.json()
                success = data.get("success", "N/A")
                content = data.get("content", {})
                has_body = bool(content.get("body_html", ""))
            except:
                success = f"Parse Error: {response.text[:100]}"
                has_body = False

            times.append(elapsed_ms)
            print(f"  耗時: {elapsed_ms:.0f}ms")
            print(f"  成功: {success}")
            print(f"  有內容: {has_body}")

        except requests.exceptions.Timeout:
            print(f"  請求超時")
        except Exception as e:
            print(f"  錯誤: {e}")

        print()

        if i < ITERATIONS:
            time.sleep(3)

    if times:
        avg = sum(times) / len(times)
        print(f"平均耗時: {avg:.0f}ms")
        print(f"最小: {min(times):.0f}ms")
        print(f"最大: {max(times):.0f}ms")

    return times


if __name__ == "__main__":
    print("本地 API 效能測試")
    print()

    # 檢查服務是否運行
    try:
        response = requests.get(f"{API_URL}/version", timeout=5)
        print(f"服務狀態: ✅ 運行中")
        print(f"版本: {response.json()}")
    except Exception as e:
        print(f"服務狀態: ❌ 未運行 ({e})")
        exit(1)

    print()
    test_api("主流程測試")
