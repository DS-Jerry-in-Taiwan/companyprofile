"""
新模組：Tavily 混合搜尋
=====================

結合批次搜尋 + 結構化欄位補充

"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


class HybridTavilySearch:
    """
    混合搜尋模組
    - 第一階段：批次取得基本資訊
    - 第二階段：補充營業項目和主要服務
    """

    def __init__(self, api_key: str = None):
        from src.services.tavily_search import TavilySearchProvider

        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key or self.api_key == "dummy_value":
            raise ValueError("TAVILY_API_KEY is required")

        self.provider = TavilySearchProvider(api_key=self.api_key)

    def search(self, company_name: str) -> Dict[str, Any]:
        """
        執行混合搜尋

        Returns:
            {
                "success": bool,
                "company_name": str,
                "unified_number": str,
                "capital": str,
                "founded_date": str,
                "address": str,
                "officer": str,
                "main_services": str,
                "business_items": str,
                "raw_answers": {...},
                "elapsed_times": {...},
                "confidence": "高/中/低",
                "missing_fields": [...]
            }
        """
        result = {
            "success": False,
            "company_name": company_name,
            "elapsed_times": {},
            "raw_answers": {},
            "confidence": "低",
            "missing_fields": [],
        }

        # ===== Step 1: 批次取得基本資訊 =====
        print(f"\n[Step 1] 批次查詢基本資訊...")

        basic_query = f"{company_name} 統一編號 資本額 成立時間 公司地址 負責人"
        start = time.time()
        basic_result = self.provider.get_search_info(basic_query, max_results=3)
        basic_elapsed = time.time() - start
        result["elapsed_times"]["basic"] = basic_elapsed

        basic_answer = basic_result.get("answer", "")
        result["raw_answers"]["basic"] = basic_answer

        print(f"  耗時: {basic_elapsed:.2f}s")
        print(f"  答案: {basic_answer[:100]}...")

        # 解析基本資訊
        result.update(self._parse_basic_info(basic_answer, company_name))

        # ===== Step 2: 補充營業項目 =====
        print(f"\n[Step 2] 補充營業項目...")

        # 檢查是否需要補充
        if (
            not result.get("business_items")
            or len(result.get("business_items", "")) < 50
        ):
            start = time.time()
            business_result = self.provider.get_search_info(
                f"{company_name} 營業項目 產品 服務", max_results=3
            )
            business_elapsed = time.time() - start
            result["elapsed_times"]["business_items"] = business_elapsed

            business_answer = business_result.get("answer", "")
            result["raw_answers"]["business_items"] = business_answer
            result["business_items"] = business_answer

            print(f"  耗時: {business_elapsed:.2f}s")
            print(f"  答案: {business_answer[:100]}...")
        else:
            result["elapsed_times"]["business_items"] = 0
            print(f"  已從基本查詢取得，無需補充")

        # ===== Step 3: 補充主要服務 =====
        print(f"\n[Step 3] 補充主要服務...")

        if not result.get("main_services") or len(result.get("main_services", "")) < 30:
            start = time.time()
            services_result = self.provider.get_search_info(
                f"{company_name} 主要產品 服務 業務", max_results=3
            )
            services_elapsed = time.time() - start
            result["elapsed_times"]["main_services"] = services_elapsed

            services_answer = services_result.get("answer", "")
            result["raw_answers"]["main_services"] = services_answer
            result["main_services"] = services_answer

            print(f"  耗時: {services_elapsed:.2f}s")
            print(f"  答案: {services_answer[:100]}...")
        else:
            result["elapsed_times"]["main_services"] = 0
            print(f"  已從基本查詢取得，無需補充")

        # ===== 計算總耗時和信心度 =====
        result["total_elapsed"] = sum(result["elapsed_times"].values())
        result["api_calls"] = len(
            [v for v in result["elapsed_times"].values() if v > 0]
        )

        # 評估資訊完整性
        required_fields = ["unified_number", "capital", "founded_date", "officer"]
        result["missing_fields"] = [
            f
            for f in required_fields
            if not result.get(f) or len(result.get(f, "")) < 5
        ]

        if len(result["missing_fields"]) == 0:
            result["confidence"] = "高"
        elif len(result["missing_fields"]) <= 2:
            result["confidence"] = "中"
        else:
            result["confidence"] = "低"

        result["success"] = True

        return result

    def _parse_basic_info(self, answer: str, company_name: str) -> Dict[str, str]:
        """解析基本資訊"""
        import re

        parsed = {}

        # 統一編號（8位數字）
        id_match = re.search(r"[0-9]{8}", answer)
        if id_match:
            parsed["unified_number"] = id_match.group(0)

        # 資本額
        capital_match = re.search(r"([0-9,]+)\s*[萬億]?元", answer)
        if capital_match:
            parsed["capital"] = capital_match.group(0)

        # 成立時間
        date_match = re.search(r"(\d{4})年", answer)
        if date_match:
            parsed["founded_date"] = f"{date_match.group(1)}年"

        # 地址
        addr_match = re.search(
            r"[高雄市台北市新北市台中市台南市].*?[路街段巷號][^。，,。\n]*", answer
        )
        if addr_match:
            parsed["address"] = addr_match.group(0)

        # 負責人
        officer_match = re.search(r"負責人[：:]\s*(\S+)", answer)
        if officer_match:
            parsed["officer"] = officer_match.group(1)

        return parsed


def test_all_strategies(company_name: str = "澳霸有限公司"):
    """測試所有搜尋策略"""

    print("=" * 70)
    print("搜 尋 策 略 全 面 比 較")
    print("=" * 70)
    print(f"\n測試公司: {company_name}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # ===== 策略一：Tavily 批次 =====
    print(f"\n{'=' * 70}")
    print(f"策 略 一：Tavily 批次搜尋")
    print(f"{'=' * 70}")

    from src.services.tavily_search import TavilySearchProvider

    tavily_provider = TavilySearchProvider()

    start = time.time()
    tavily_batch_result = tavily_provider.get_search_info(
        f"{company_name} 統一編號、資本額、成立時間、地址、負責人、主要服務、營業項目",
        max_results=3,
    )
    tavily_batch_time = time.time() - start

    results["tavily_batch"] = {
        "success": True,
        "elapsed": tavily_batch_time,
        "api_calls": 1,
        "answer": tavily_batch_result.get("answer", ""),
        "answer_length": len(tavily_batch_result.get("answer", "")),
    }

    print(f"\n⏱️  耗時: {tavily_batch_time:.2f}s")
    print(f"📝 Answer ({len(tavily_batch_result.get('answer', ''))} 字):")
    print(f"  {tavily_batch_result.get('answer', '')}")

    # ===== 策略二：Gemini Few-shot + Validate =====
    print(f"\n{'=' * 70}")
    print(f"策 略 二：Gemini Few-shot + Validate")
    print(f"{'=' * 70}")

    from google import genai
    from google.genai import types

    GEMINI_PROMPT = f"""你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "公司名稱",
    "unified_number": "統一編號（8位數字）",
    "capital": "資本額",
    "founded_date": "成立時間",
    "address": "公司地址",
    "officer": "負責人",
    "main_services": "主要服務",
    "business_items": "營業項目詳細"
}}

請搜尋並回覆 JSON。"""

    api_key = os.getenv("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    start = time.time()
    gemini_response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=GEMINI_PROMPT,
        config=types.GenerateContentConfig(
            tools=[search_tool],
            temperature=0.2,
        ),
    )
    gemini_time = time.time() - start

    # 解析 JSON
    import re

    json_match = re.search(
        r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", gemini_response.text, re.DOTALL
    )

    results["gemini_fewshot"] = {
        "success": True,
        "elapsed": gemini_time,
        "api_calls": 1,
        "answer": gemini_response.text,
        "answer_length": len(gemini_response.text),
        "json_parsed": json_match.group(0) if json_match else None,
    }

    print(f"\n⏱️  耗時: {gemini_time:.2f}s")
    print(f"📝 Answer ({len(gemini_response.text)} 字):")
    print(f"  {gemini_response.text[:300]}...")

    # ===== 策略三：Tavily 混合（新模組）=====
    print(f"\n{'=' * 70}")
    print(f"策 略 三：Tavily 混合搜尋（新模組）")
    print(f"{'=' * 70}")

    try:
        hybrid_search = HybridTavilySearch()
        hybrid_result = hybrid_search.search(company_name)
        results["tavily_hybrid"] = hybrid_result

        print(f"\n⏱️  總耗時: {hybrid_result.get('total_elapsed', 0):.2f}s")
        print(f"📞 API 呼叫次數: {hybrid_result.get('api_calls', 0)}")
        print(f"📊 資訊完整性:")
        print(f"  - 統一編號: {hybrid_result.get('unified_number', 'N/A')}")
        print(f"  - 資本額: {hybrid_result.get('capital', 'N/A')}")
        print(f"  - 成立時間: {hybrid_result.get('founded_date', 'N/A')}")
        print(f"  - 地址: {hybrid_result.get('address', 'N/A')}")
        print(f"  - 負責人: {hybrid_result.get('officer', 'N/A')}")
        print(f"  - 主要服務: {hybrid_result.get('main_services', 'N/A')[:50]}...")
        print(f"  - 營業項目: {hybrid_result.get('business_items', 'N/A')[:50]}...")
        print(f"  - 信心度: {hybrid_result.get('confidence', 'N/A')}")

    except Exception as e:
        print(f"❌ Tavily 混合搜尋失敗: {e}")
        results["tavily_hybrid"] = {"success": False, "error": str(e)}

    # ===== 比較總結 =====
    print(f"\n{'=' * 70}")
    print(f"比 較 總 結")
    print(f"{'=' * 70}")

    print(f"\n📊 耗時比較:")
    print(
        f"  策略一（Tavily 批次）:    {results['tavily_batch']['elapsed']:.2f}s ({results['tavily_batch']['api_calls']} 次 API)"
    )
    print(
        f"  策略二（Gemini Few-shot）: {results['gemini_fewshot']['elapsed']:.2f}s ({results['gemini_fewshot']['api_calls']} 次 API)"
    )
    if results.get("tavily_hybrid", {}).get("success"):
        print(
            f"  策略三（Tavily 混合）:    {results['tavily_hybrid']['total_elapsed']:.2f}s ({results['tavily_hybrid']['api_calls']} 次 API)"
        )

    print(f"\n📊 資訊長度比較:")
    print(f"  策略一（Tavily 批次）:    {results['tavily_batch']['answer_length']} 字")
    print(
        f"  策略二（Gemini Few-shot）: {results['gemini_fewshot']['answer_length']} 字"
    )
    if results.get("tavily_hybrid", {}).get("success"):
        total_len = (
            len(results["tavily_hybrid"].get("unified_number", "") or "")
            + len(results["tavily_hybrid"].get("capital", "") or "")
            + len(results["tavily_hybrid"].get("founded_date", "") or "")
            + len(results["tavily_hybrid"].get("address", "") or "")
            + len(results["tavily_hybrid"].get("officer", "") or "")
            + len(results["tavily_hybrid"].get("main_services", "") or "")
            + len(results["tavily_hybrid"].get("business_items", "") or "")
        )
        print(f"  策略三（Tavily 混合）:    {total_len} 字（結構化解析）")

    print(f"\n📊 格式比較:")
    print(f"  策略一（Tavily 批次）:    自然語言，需要自己解析")
    print(f"  策略二（Gemini Few-shot）: JSON 格式，直接可用 ✅")
    print(f"  策略三（Tavily 混合）:    結構化欄位，直接可用 ✅")

    print(f"\n💡 建議:")
    if results.get("tavily_hybrid", {}).get("success"):
        th = results["tavily_hybrid"]
        if th["confidence"] == "高" and th["total_elapsed"] < 10:
            print(f"  → 推薦使用「策略三（Tavily 混合）」：速度快、資訊完整、費用低")
        elif th["confidence"] == "中":
            print(f"  → 可考慮「策略二（Gemini Few-shot）」：格式最整潔")
    print(f"  → 如果需要最高資訊完整性 → 策略二（Gemini Few-shot）")
    print(f"  → 如果需要最快速度 → 策略三（Tavily 混合）")

    # 儲存結果
    output = {
        "company_name": company_name,
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }

    output_path = os.path.join(
        PROJECT_ROOT, "scripts", "stage3_test", "all_strategies_comparison.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n\n📁 完整結果已儲存至: {output_path}")

    return results


if __name__ == "__main__":
    test_all_strategies("澳霸有限公司")
