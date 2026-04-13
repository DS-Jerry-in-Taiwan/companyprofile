"""
測試：Gemini Search + Few-shot + Validate
"""

import os
import sys
import json
import time

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from google import genai
from google.genai import types


# ===== Few-shot Prompt =====
FEWSHOT_SEARCH_PROMPT = """你是一個公司資訊搜尋專家。請搜尋並整理以下公司的資訊。

【輸出格式要求 - 請嚴格遵守】
請以以下 JSON 格式回覆：
{{
    "company_name": "公司名稱",
    "unified_number": "統一編號（8位數字）",
    "capital": "資本額（數字+貨幣單位）",
    "founded_date": "成立時間（西元年份）",
    "address": "公司地址",
    "main_services": ["服務1", "服務2"],
    "business_items": ["營業項目1", "營業項目2"],
    "officer": "負責人姓名",
    "information_confidence": "高/中/低",
    "missing_info": ["缺失的資訊1"]
}}

【範例】
輸入：搜尋「台積電」資訊
輸出：
{{
    "company_name": "台灣積體電路製造股份有限公司",
    "unified_number": "22099131",
    "capital": "新台幣 283,218,380,610 元",
    "founded_date": "1987年",
    "address": "新竹科學工業園區力行六路10號",
    "main_services": ["積體電路製造", "半導體封裝", "測試服務"],
    "business_items": ["積體電路製造及銷售", "半導體封裝及測試", "相關技術服務"],
    "officer": "魏哲家",
    "information_confidence": "高",
    "missing_info": []
}}

現在請搜尋以下公司：{query}"""

# ===== Validate Prompt =====
VALIDATE_PROMPT = """請檢查以下公司資訊是否完整：

{collected_info}

【必要資訊檢查清單】
1. 統一編號（8位數字） - 必需
2. 資本額（數字） - 必需
3. 成立時間（年份） - 必需
4. 主要產品/服務 - 必需
5. 負責人 - 必需
6. 公司地址 - 可選

【檢查規則】
- 如果有任何「必需」項目缺失，information_confidence 只能是「低」
- 統一編號必須是 8 位數字
- 資本額必須是數字（可能帶貨幣單位）

【輸出格式】
只回覆 JSON：
{{
    "is_complete": true/false,
    "confidence": "高/中/低",
    "missing_required": ["缺失的必需項目"],
    "suspicious_items": ["可疑的項目"]
}}"""

# ===== Gemini Search Tool =====
SEARCH_TOOL = types.Tool(google_search=types.GoogleSearch())


def test_gemini_with_fewshot(query: str = "澳霸有限公司"):
    """測試 Gemini + Few-shot"""

    print(f"\n{'=' * 60}")
    print(f"測試：Gemini + Few-shot")
    print(f"{'=' * 60}")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Gemini API Key 未設定")
        return None

    client = genai.Client(api_key=api_key)

    # 1. 用 Few-shot 搜尋
    print(f"\n📝 Step 1: Few-shot 搜尋...")
    prompt = FEWSHOT_SEARCH_PROMPT.format(query=query)

    start = time.time()
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[SEARCH_TOOL],
            temperature=0.2,
        ),
    )
    search_time = time.time() - start

    text = response.text
    print(f"⏱️  搜尋耗時: {search_time:.2f} 秒")
    print(f"📝 回應長度: {len(text)} 字")

    # 解析 JSON
    try:
        # 嘗試從回應中提取 JSON
        json_str = extract_json(text)
        if json_str:
            result = json.loads(json_str)
            print(f"\n✅ JSON 解析成功")
            print(f"\n📊 搜尋結果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n⚠️ 無法解析 JSON，回應內容:")
            print(text[:500])
            result = {"raw_text": text}
    except Exception as e:
        print(f"\n❌ JSON 解析失敗: {e}")
        result = {"raw_text": text}

    # 2. 用 Validate 驗證
    print(f"\n\n📝 Step 2: Validate 驗證...")

    if "raw_text" not in result:
        validate_prompt = VALIDATE_PROMPT.format(
            collected_info=json.dumps(result, ensure_ascii=False)
        )

        start = time.time()
        validate_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=validate_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
            ),
        )
        validate_time = time.time() - start

        print(f"⏱️  驗證耗時: {validate_time:.2f} 秒")

        try:
            validate_json_str = extract_json(validate_response.text)
            if validate_json_str:
                validate_result = json.loads(validate_json_str)
                print(f"\n✅ 驗證結果:")
                print(json.dumps(validate_result, ensure_ascii=False, indent=2))

                # 合併結果
                result["validation"] = validate_result
        except Exception as e:
            print(f"⚠️ 驗證解析失敗: {e}")

    result["search_time"] = search_time
    result["total_time"] = search_time + (
        validate_time if "validate_time" in dir() else 0
    )

    return result


def extract_json(text: str) -> str:
    """從文字中提取 JSON"""
    # 嘗試找 {...} 區塊
    import re

    # 匹配 { ... } 包括多行
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return None


def main():
    print("=" * 60)
    print("Gemini Search + Few-shot + Validate 測試")
    print("=" * 60)

    query = "澳霸有限公司"
    print(f"\n測試公司: {query}")

    # 測試
    result = test_gemini_with_fewshot(query)

    # 儲存結果
    output_path = os.path.join(
        PROJECT_ROOT, "scripts", "stage3_test", "gemini_fewshot_validate_result.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n\n📁 結果已儲存至: {output_path}")

    # 比較總結
    print(f"\n{'=' * 60}")
    print(f"總結")
    print(f"{'=' * 60}")
    print(f"搜尋耗時: {result.get('search_time', 'N/A'):.2f} 秒")
    print(f"總耗時: {result.get('total_time', 'N/A'):.2f} 秒")


if __name__ == "__main__":
    main()
