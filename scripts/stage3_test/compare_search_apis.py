"""
Tavily vs Gemini Search 比較測試
=================================

測試目的：比較兩種搜尋 API 的效果

測試公司：澳霸有限公司

"""

import os
import sys
import time
import json
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def test_tavily_search(query: str, max_results: int = 5):
    """測試 Tavily 搜尋"""
    from src.services.tavily_search import TavilySearchProvider

    print(f"\n{'=' * 60}")
    print(f"TAVILY 搜尋測試")
    print(f"{'=' * 60}")

    api_key = os.getenv("TAVILY_API_KEY")
    print(f"API Key: {'*' * 20}{api_key[-4:] if api_key else 'Not found'}")
    print(f"Query: {query}")
    print(f"Max Results: {max_results}")

    if not api_key or api_key == "dummy_value":
        print("❌ Tavily API Key 未設定或無效")
        return None

    try:
        provider = TavilySearchProvider(api_key=api_key)
        start_time = time.time()
        result = provider.get_search_info(query, max_results)
        elapsed = time.time() - start_time

        print(f"\n⏱️  耗時: {elapsed:.2f} 秒")
        print(f"\n📊 結果:")
        print(f"  - 成功: {result.get('success', 'N/A')}")
        print(f"  - 結果數量: {len(result.get('results', []))}")

        # AI 生成的答案
        answer = result.get("answer")
        if answer:
            print(f"\n🤖 AI 答案摘要:")
            print(f"  {answer[:500]}...")
        else:
            print(f"\n🤖 AI 答案摘要: 無")

        # 前3個搜尋結果
        print(f"\n📋 搜尋結果 (前3個):")
        for i, r in enumerate(result.get("results", [])[:3], 1):
            print(f"\n  [{i}] {r.get('title', 'N/A')}")
            print(f"      URL: {r.get('url', 'N/A')}")
            content = r.get("content", "")
            print(
                f"      內容: {content[:200]}..."
                if len(content) > 200
                else f"      內容: {content}"
            )

        return result

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return None


def test_gemini_search(query: str, max_results: int = 5):
    """測試 Gemini Search (使用 Gemini 2.0 Flash 的內建搜尋能力)"""
    from google import genai
    from google.genai import types

    print(f"\n{'=' * 60}")
    print(f"GEMINI SEARCH 測試 (Gemini 2.0 Flash with Search)")
    print(f"{'=' * 60}")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
    print(f"API Key: {'*' * 20}{api_key[-4:] if api_key else 'Not found'}")
    print(f"Query: {query}")
    print(f"Max Results: {max_results}")

    if not api_key:
        print("❌ Gemini API Key 未設定")
        return None

    try:
        client = genai.Client(api_key=api_key)

        # Gemini 2.0 Flash with Search
        model_name = "gemini-2.0-flash"

        # 使用 Gemini 的搜尋工具 (Google Search Grounding)
        # 使用 types.Tool 包裝 types.GoogleSearch
        search_tool = types.Tool(google_search=types.GoogleSearch())

        print(f"\n模型: {model_name}")
        print(f"工具: GoogleSearchRetrieval (Google Search Grounding)")

        # 設定搜尋工具

        start_time = time.time()

        # 產生搜尋查詢
        response = client.models.generate_content(
            model=model_name,
            contents=f"請搜尋「{query}」的相關資訊，包括公司官網、成立時間、資本額、主要產品和服務、營運狀況等。請盡量收集詳細的資訊。",
            config=types.GenerateContentConfig(
                tools=[search_tool],
                temperature=0.3,
            ),
        )

        elapsed = time.time() - start_time

        print(f"\n⏱️  耗時: {elapsed:.2f} 秒")

        # 檢查是否有 groundings (搜尋結果)
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]

            # 取得 grounding 資訊
            if (
                hasattr(candidate, "grounding_metadata")
                and candidate.grounding_metadata
            ):
                grounding = candidate.grounding_metadata

                # 取得搜尋查詢
                queries = (
                    grounding.grounding_chunks
                    if hasattr(grounding, "grounding_chunks")
                    else []
                )

                print(f"\n📊 結果:")
                print(f"  - 生成完成: True")

                # 顯示 Grounding 來源
                if hasattr(grounding, "grounding_attributions"):
                    attributions = grounding.grounding_attributions
                    print(f"\n🔗 引用來源 ({len(attributions)} 個):")
                    for i, attr in enumerate(attributions[:3], 1):
                        if hasattr(attr, "source") and hasattr(attr.source, "uri"):
                            print(f"  [{i}] {attr.source.uri}")
                        elif hasattr(attr, "source"):
                            print(f"  [{i}] {attr.source}")

                # 嘗試取得網頁內容
                if hasattr(grounding, "web_search_sources"):
                    sources = grounding.web_search_sources
                    print(f"\n🌐 Web Search Sources:")
                    for src in sources[:3]:
                        print(f"  - {src}")
            else:
                print(f"\n📊 結果:")
                print(f"  - 生成完成: True")
                print(f"  - Grounding Metadata: 無")

        # 顯示回應內容
        print(f"\n🤖 Gemini 回應:")
        text = response.text
        print(f"  {text[:800]}..." if len(text) > 800 else f"  {text}")

        return {"success": True, "text": text, "model": model_name, "elapsed": elapsed}

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback

        traceback.print_exc()
        return None


def compare_results(tavily_result, gemini_result):
    """比較兩個搜尋結果"""
    print(f"\n{'=' * 60}")
    print(f"結 果 比 較 (客觀資料)")
    print(f"{'=' * 60}")

    # Tavily 資料
    print(f"\n📊 Tavily:")
    if tavily_result:
        answer = tavily_result.get("answer", "")
        results = tavily_result.get("results", [])
        print(
            f"  - AI 摘要: {'有' if answer else '無'} ({len(answer)} 字)"
            if answer
            else f"  - AI 摘要: 無"
        )
        print(f"  - 搜尋結果數量: {len(results)}")
        print(f"  - 結果來源:")
        for r in results[:3]:
            print(f"      * {r.get('title', 'N/A')[:50]}")
    else:
        print(f"  - 搜尋失敗")

    # Gemini 資料
    print(f"\n📊 Gemini:")
    if gemini_result:
        text = gemini_result.get("text", "")
        elapsed = gemini_result.get("elapsed", 0)
        print(f"  - 回應長度: {len(text)} 字")
        print(f"  - 耗時: {elapsed:.2f} 秒")
        print(f"  - 回應內容預覽:")
        preview = text[:300] + "..." if len(text) > 300 else text
        print(f"    {preview}")
    else:
        print(f"  - 搜尋失敗或未測試")

    print(f"\n💡 請自行比較上述資料，判斷哪個更符合需求")


def main():
    print("=" * 60)
    print("Tavily vs Gemini Search 比較測試")
    print("=" * 60)

    # 測試查詢 - 用同一個公司
    query = "澳霸有限公司"
    max_results = 5

    print(f"\n測試公司: {query}")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 測試 Tavily
    tavily_result = test_tavily_search(query, max_results)

    # 測試 Gemini
    gemini_result = test_gemini_search(query, max_results)

    # 比較結果
    compare_results(tavily_result, gemini_result)

    # 儲存結果
    output = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "tavily": tavily_result,
        "gemini": gemini_result,
    }

    output_path = os.path.join(
        PROJECT_ROOT, "scripts", "stage3_test", "search_comparison_results.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n\n📁 完整結果已儲存至: {output_path}")


if __name__ == "__main__":
    main()
