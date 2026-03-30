"""
Checkpoint 2 - LLM 輸出品質驗證腳本
執行方式: source venv/bin/activate && python tests/checkpoint2_verify.py
"""

import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from src.services.llm_service import LLMService
from src.utils.token_manager import TokenManager


def test_generate_mode():
    print("=" * 60)
    print("【測試 1】生成模式 - 僅憑公司資訊產出簡介")
    print("=" * 60)

    company_data = {
        "company_name": "鴻海科技集團",
        "industry": "電子製造服務",
        "description": "全球最大電子代工製造商，專注於電子產品組裝與製造",
        "products_services": "消費電子、雲端網路、電腦終端、元件及其他",
        "company_size": "超過 80 萬名員工",
        "founded_year": "1974",
    }

    service = LLMService()
    result = service.generate(company_data)

    print(f"\n標題: {result.title}")
    print(f"摘要: {result.summary}")
    print(f"正文:\n{result.body_html}")
    print(f"\n[Token 統計]")
    tm = TokenManager()
    print(f"標題 Token: {tm.count_tokens(result.title)}")
    print(f"摘要 Token: {tm.count_tokens(result.summary)}")
    print(f"正文 Token: {tm.count_tokens(result.body_html)}")
    return result


def test_optimize_mode():
    print("\n" + "=" * 60)
    print("【測試 2】優化模式 - 擴展現有簡介")
    print("=" * 60)

    original = "台積電是全球最大的晶圓代工廠，創辦人為張忠謀。"
    additional_data = {
        "company_name": "台積電",
        "industry": "半導體製造",
        "additional_info": "專注於先進製程技術，客戶包含 Apple、NVIDIA 等",
        "products_services": "晶圓代工、先進封裝、光罩製作",
    }

    service = LLMService()
    result = service.optimize(original, additional_data)

    print(f"\n原始簡介: {original}")
    print(f"\n優化後標題: {result.title}")
    print(f"優化後摘要: {result.summary}")
    print(f"優化後正文:\n{result.body_html}")
    return result


def evaluate_result(result, mode):
    print(f"\n{'=' * 60}")
    print(f"【{mode} 品質評估】")
    print("=" * 60)
    checks = {
        "標題長度 10-30 字": 10 <= len(result.title) <= 30,
        "摘要長度 ≤50 字": len(result.summary) <= 50,
        "正文包含 HTML 標籤": "<p>" in result.body_html,
        "標題非空": len(result.title) > 0,
        "摘要非空": len(result.summary) > 0,
        "正文非空": len(result.body_html) > 0,
    }
    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check}")
    return all(checks.values())


if __name__ == "__main__":
    print("Checkpoint 2 - LLM 輸出品質驗證\n")

    try:
        r1 = test_generate_mode()
        p1 = evaluate_result(r1, "生成模式")

        r2 = test_optimize_mode()
        p2 = evaluate_result(r2, "優化模式")

        print(f"\n{'=' * 60}")
        print("【最終結果】")
        print("=" * 60)
        print(f"  生成模式: {'PASS' if p1 else 'FAIL'}")
        print(f"  優化模式: {'PASS' if p2 else 'FAIL'}")
        if p1 and p2:
            print("\n✅ Checkpoint 2 通過，可進入 Phase 4")
        else:
            print("\n❌ Checkpoint 2 未通過，需調整 Prompt 或邏輯")
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
