#!/usr/bin/env python3
"""
API Server Entry Point
用法:
  python run_api.py          # 啟動服務
  python run_api.py test     # 測試模式
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FUNCTIONS_DIR = os.path.join(PROJECT_ROOT, "src", "functions")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 測試模式
        sys.path.insert(0, FUNCTIONS_DIR)

        from utils.generate_brief import generate_brief
        from utils.request_validator import validate_request

        data = {
            "organNo": "69188618",
            "organ": "私立揚才文理短期補習班",
            "mode": "GENERATE",
        }

        valid_data = validate_request(data)
        result = generate_brief(valid_data)

        print("=" * 60)
        print("【生成的簡介】")
        print("=" * 60)
        print(f"Title: {result.get('title', '')}")
        print(f"Summary: {result.get('summary', '')}")

    else:
        # 啟動 Flask 服務
        sys.path.insert(0, FUNCTIONS_DIR)
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

        os.chdir(FUNCTIONS_DIR)

        import api_controller

        app = api_controller.app

        # 使用 app.run() 而不是 subprocess，這樣 Ctrl+C 可以優雅關閉
        try:
            app.run(debug=False, host="0.0.0.0", port=5000, use_reloader=False)
        except KeyboardInterrupt:
            print("\n服務已關閉")


if __name__ == "__main__":
    main()
