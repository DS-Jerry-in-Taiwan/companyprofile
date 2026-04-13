"""
分析 Tavily 返回的資料結構
"""

import os
import sys
import json

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.services.tavily_search import TavilySearchProvider


def analyze_tavily_structure(query: str = "澳霸有限公司"):
    """分析 Tavily 返回的完整資料結構"""

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key == "dummy_value":
        print("❌ Tavily API Key 無效")
        return

    provider = TavilySearchProvider(api_key=api_key)

    print(f"\n{'=' * 60}")
    print(f"Tavily 完整資料結構分析")
    print(f"{'=' * 60}")
    print(f"\n查詢: {query}")

    # 取得完整結果
    result = provider.get_search_info(query, max_results=3)

    print(f"\n📦 頂層結構:")
    print(f"  keys: {list(result.keys())}")

    # 1. Answer (AI 摘要)
    print(f"\n1️⃣  'answer' (AI 生成的摘要):")
    print(f"    type: {type(result.get('answer'))}")
    print(f"    length: {len(result.get('answer', ''))} 字")
    print(f"    content:\n{result.get('answer', 'N/A')}")

    # 2. Results (搜尋結果列表)
    print(f"\n2️⃣  'results' (搜尋結果列表):")
    results = result.get("results", [])
    print(f"    type: {type(results)}")
    print(f"    count: {len(results)}")

    if results:
        print(f"\n    第一個結果的結構:")
        first = results[0]
        print(f"      keys: {list(first.keys())}")
        print(f"\n    第一個結果的完整內容:")
        print(json.dumps(first, ensure_ascii=False, indent=4))

    # 3. 其他欄位
    print(f"\n3️⃣  其他欄位:")
    for key in result.keys():
        if key not in ["answer", "results"]:
            val = result[key]
            if isinstance(val, (list, dict)):
                print(
                    f"    '{key}': {type(val)}, len={len(val) if hasattr(val, '__len__') else 'N/A'}"
                )
            else:
                print(f"    '{key}': {val}")

    return result


def design_gemini_search_with_fewshot():
    """
    設計：Gemini Search + Few-shot + Validate 流程

    概念：
    1. 用 Few-shot 指定輸出的結構化格式
    2. 用 Validate 檢查必要資訊是否齊全
    3. 如果不完整，讓 LLM 自動補充
    """

    print(f"\n{'=' * 60}")
    print(f"Gemini Search + Few-shot + Validate 設計")
    print(f"{'=' * 60}")

    # Few-shot Prompt Template
    fewshot_prompt = """
你是一個公司資訊搜尋專家。請搜尋並整理以下公司的資訊。

【輸出格式要求 - 請嚴格遵守】
請以以下 JSON 格式回覆：
{
    "company_name": "公司名稱",
    "unified_number": "統一編號（8位數字）",
    "capital": "資本額（數字+貨幣單位）",
    "founded_date": "成立時間（西元年份）",
    "address": "公司地址",
    "main_services": ["服務1", "服務2", ...],
    "business_items": ["營業項目1", "營業項目2", ...],
    "information_confidence": "高/中/低",
    "missing_info": ["缺失的資訊1", "缺失的資訊2"]
}

【範例】
輸入：搜尋「台積電」資訊
輸出：
{
    "company_name": "台灣積體電路製造股份有限公司",
    "unified_number": "22099131",
    "capital": "新台幣 283,218,380,610 元",
    "founded_date": "1987年",
    "address": "新竹科學工業園區力行六路10號",
    "main_services": ["積體電路製造", "半導體封裝", "測試服務"],
    "business_items": ["積體電路製造及銷售", "半導體封裝及測試", "相關技術服務"],
    "information_confidence": "高",
    "missing_info": []
}

現在請搜尋以下公司：
"""

    validate_prompt = """
請檢查以下公司資訊是否完整：

{collected_info}

【必要資訊檢查清單】
1. 統一編號（8位數字） - 必需
2. 資本額（數字） - 必需
3. 成立時間（年份） - 必需
4. 主要產品/服務 - 必需
5. 公司地址 - 可選

【檢查規則】
- 如果有任何「必需」項目缺失，請在 missing_info 中標示
- 如果資訊明顯錯誤（如統編不是8位數），請標示為可疑
- information_confidence 欄位：
  - 高：所有必需項目都有，且資料來源可靠
  - 中：大部分資訊齊全，少數資訊缺失或來源不明
  - 低：嚴重資訊缺失或來源不可靠

【輸出格式】
{
    "is_complete": true/false,
    "confidence": "高/中/低",
    "missing_required": ["缺失的必需項目"],
    "suspicious_items": ["可疑的項目"],
    "suggestions": ["補充建議"]
}

如果 is_complete=false，請同時提供補充後的完整資訊。
"""

    print(f"\n📝 FEW-SHOT PROMPT:")
    print(fewshot_prompt)

    print(f"\n\n📝 VALIDATE PROMPT:")
    print(validate_prompt)

    return fewshot_prompt, validate_prompt


if __name__ == "__main__":
    # 分析 Tavily 結構
    tavily_result = analyze_tavily_structure("澳霸有限公司")

    # 設計 Gemini + Few-shot + Validate
    fewshot_prompt, validate_prompt = design_gemini_search_with_fewshot()

    # 儲存結果
    output = {
        "tavily_result_structure": {
            "keys": list(tavily_result.keys()) if tavily_result else [],
            "answer_length": len(tavily_result.get("answer", ""))
            if tavily_result
            else 0,
            "results_count": len(tavily_result.get("results", []))
            if tavily_result
            else 0,
        },
        "gemini_fewshot_prompt": fewshot_prompt,
        "gemini_validate_prompt": validate_prompt,
    }

    output_path = os.path.join(
        PROJECT_ROOT, "scripts", "stage3_test", "search_structure_analysis.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n\n📁 分析結果已儲存至: {output_path}")
