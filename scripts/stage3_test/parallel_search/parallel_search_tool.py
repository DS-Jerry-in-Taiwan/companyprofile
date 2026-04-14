"""
平行搜尋工具 (Parallel Search Tool)
====================================

目標：在測試區驗證平行執行多個搜尋工具的概念

設計：
1. ParallelMultiSourceTool - 同時執行多個搜尋工具
2. 取最快結果 + 多源交叉驗證
3. 回傳信心度指標

與現有工具的介面相容：
- 輸入：query (公司名稱)
- 輸出：SearchResult
"""

import os
import sys
import time
import json
import concurrent.futures
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# 取得專案根目錄
_CURRENT_FILE = os.path.abspath(__file__)
# scripts/stage3_test/parallel_search/parallel_search_tool.py
# 往上 4 層: parallel_search -> stage3_test -> scripts -> 專案根目錄
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


# ===== 搜尋結果資料類別 =====
@dataclass
class SearchResult:
    """統一搜尋結果格式（與 search_tools.py 相容）"""

    success: bool
    tool_type: str
    elapsed_time: float
    api_calls: int
    data: Dict[str, Any]
    raw_answer: str
    answer_length: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "tool_type": self.tool_type,
            "elapsed_time": self.elapsed_time,
            "api_calls": self.api_calls,
            "data": self.data,
            "raw_answer": self.raw_answer,
            "answer_length": self.answer_length,
        }


# ===== 工具類型枚舉 =====
class SearchToolType:
    """支援的搜尋工具類型"""

    PARALLEL_MULTI_SOURCE = "parallel_multi_source"
    TAVILY = "tavily"
    GEMINI_FEWSHOT = "gemini_fewshot"


# ===== Tavily 工具包裝 =====
class TavilySearchTool:
    """Tavily 搜尋工具包裝"""

    tool_name = "TavilyBatchSearchTool"

    def __init__(self, **kwargs):
        self.max_results = kwargs.get("max_results", 3)
        self.include_answer = kwargs.get("include_answer", True)

        from src.services.tavily_search import TavilySearchProvider

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key or api_key == "dummy_value":
            raise ValueError("TAVILY_API_KEY is required")

        self.provider = TavilySearchProvider(
            api_key=api_key,
            max_results=self.max_results,
            include_answer=self.include_answer,
        )

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行 Tavily 搜尋"""
        import re

        # 組合查詢
        fields_query = "統一編號、資本額、成立時間、公司地址、負責人、主要服務"
        full_query = f"{query} 的 {fields_query}"

        start = time.time()
        result = self.provider.get_search_info(full_query, max_results=self.max_results)
        elapsed = time.time() - start

        answer = result.get("answer", "")

        self._last_metadata = {
            "query": full_query,
            "total_results": len(result.get("results", [])),
        }

        return SearchResult(
            success=True,
            tool_type=SearchToolType.TAVILY,
            elapsed_time=elapsed,
            api_calls=1,
            data={"answer": answer, "results": result.get("results", [])},
            raw_answer=answer,
            answer_length=len(answer),
        )


# ===== Gemini Few-shot 工具包裝 =====
class GeminiSearchTool:
    """Gemini 搜尋工具包裝"""

    tool_name = "GeminiFewShotSearchTool"

    PROMPT_TEMPLATE = """你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "公司名稱",
    "unified_number": "統一編號",
    "capital": "資本額",
    "founded_date": "成立時間",
    "address": "公司地址",
    "officer": "負責人",
    "main_services": "主要服務"
}}

請搜尋並回覆 JSON。"""

    def __init__(self, **kwargs):
        from google import genai
        from google.genai import types

        self.model = kwargs.get("model", "gemini-2.0-flash")
        self.temperature = kwargs.get("temperature", 0.2)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self._types = types
        self.search_tool = types.Tool(google_search=types.GoogleSearch())

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行 Gemini 搜尋"""
        import re

        prompt = self.PROMPT_TEMPLATE.format(company_name=query)

        start = time.time()
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                tools=[self.search_tool],
                temperature=self.temperature,
            ),
        )
        elapsed = time.time() - start

        raw_answer = response.text

        # 解析 JSON
        json_match = re.search(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw_answer, re.DOTALL
        )

        data = {}
        if json_match:
            try:
                data = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                data = {"raw": raw_answer[:500]}
        else:
            data = {"raw": raw_answer[:500]}

        return SearchResult(
            success=True,
            tool_type=SearchToolType.GEMINI_FEWSHOT,
            elapsed_time=elapsed,
            api_calls=1,
            data=data,
            raw_answer=raw_answer,
            answer_length=len(raw_answer),
        )


# ===== 平行多來源搜尋工具 =====
class ParallelMultiSourceTool:
    """
    平行多來源搜尋工具

    設計：
    1. 同時執行多個搜尋工具（Tavily + Gemini）
    2. 取所有結果 + 多源交叉驗證
    3. 回傳信心度指標
    """

    tool_name = "ParallelMultiSourceTool"

    def __init__(self, **kwargs):
        """
        初始化平行搜尋工具

        Args:
            sources: 要平行執行的工具列表
            timeout: 總超時時間（秒）
            confidence_threshold: 信心度閾值
        """
        self.sources = kwargs.get("sources", ["tavily", "gemini_fewshot"])
        self.timeout = kwargs.get("timeout", 15)
        self.confidence_threshold = kwargs.get("confidence_threshold", 0.6)

        print(f"\n🔧 ParallelMultiSourceTool 初始化")
        print(f"   來源: {self.sources}")
        print(f"   超時: {self.timeout}s")

    def search(self, query: str, **kwargs) -> SearchResult:
        """
        執行平行搜尋

        Args:
            query: 搜尋查詢（公司名稱）
            **kwargs: 額外參數

        Returns:
            SearchResult: 合併後的搜尋結果
        """
        start = time.time()

        # 建立工具
        tools = []
        for source in self.sources:
            if source == "tavily":
                tools.append(("tavily", TavilySearchTool()))
            elif source == "gemini_fewshot":
                tools.append(("gemini", GeminiSearchTool()))

        print(f"\n📤 平行搜尋開始")
        print(f"   Query: {query}")
        print(f"   工具數量: {len(tools)}")

        # 平行執行
        results = []
        errors = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tools)) as executor:
            futures = {
                executor.submit(tool.search, query): name for name, tool in tools
            }

            for future in concurrent.futures.as_completed(
                futures, timeout=self.timeout
            ):
                name = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"   ✅ {name} 完成，耗時 {result.elapsed_time:.2f}s")
                except Exception as e:
                    errors.append({"source": name, "error": str(e)})
                    print(f"   ❌ {name} 失敗: {e}")

        elapsed = time.time() - start

        # 合併結果
        if results:
            merged_data = self._merge_results(results)
            confidence = self._calculate_confidence(results)
        else:
            merged_data = {"error": "所有工具都失敗"}
            confidence = 0.0

        # 組合 metadata
        metadata = {
            "_confidence": confidence,
            "_sources": [r.tool_type for r in results],
            "_sources_count": len(results),
            "_errors": errors,
            "_elapsed_breakdown": {r.tool_type: r.elapsed_time for r in results},
        }

        print(f"\n📊 平行搜尋結果")
        print(f"   總耗時: {elapsed:.2f}s")
        print(f"   成功來源: {len(results)}/{len(tools)}")
        print(f"   信心度: {confidence}")

        return SearchResult(
            success=len(results) > 0,
            tool_type=SearchToolType.PARALLEL_MULTI_SOURCE,
            elapsed_time=elapsed,
            api_calls=sum(r.api_calls for r in results),
            data={**merged_data, **metadata},
            raw_answer=json.dumps(merged_data, ensure_ascii=False),
            answer_length=len(json.dumps(merged_data)),
        )

    def _merge_results(self, results: List[SearchResult]) -> Dict[str, Any]:
        """合併多個來源的結果"""
        if not results:
            return {}

        merged = {}

        # 收集所有來源的有效欄位
        for result in results:
            if result.success and result.data:
                for key, value in result.data.items():
                    if key not in merged:
                        merged[key] = value
                    elif merged[key] != value and value:
                        # 發現差異，標記
                        merged[f"{key}_source_a"] = merged[key]
                        merged[f"{key}_source_b"] = value
                        merged[f"{key}_conflict"] = True

        return merged

    def _calculate_confidence(self, results: List[SearchResult]) -> float:
        """計算信心度"""
        if not results:
            return 0.0

        # 來源數量權重 (40%)
        source_score = min(len(results) / 2, 1.0) * 0.4

        # 回應完整性權重 (60%)
        completeness = sum(
            1 for r in results if r.success and r.data and len(r.data) > 0
        ) / len(results)

        return round(source_score + completeness * 0.6, 2)


# ===== 便捷函式 =====
def parallel_search(query: str, sources: List[str] = None) -> SearchResult:
    """
    便捷函式：執行平行搜尋

    Args:
        query: 搜尋查詢（公司名稱）
        sources: 要使用的工具列表

    Returns:
        SearchResult: 搜尋結果
    """
    if sources is None:
        sources = ["tavily", "gemini_fewshot"]

    tool = ParallelMultiSourceTool(sources=sources)
    return tool.search(query)


# ===== 工廠函式（與現有工具相容）=====
def create_parallel_tool(**kwargs) -> ParallelMultiSourceTool:
    """創建平行搜尋工具"""
    return ParallelMultiSourceTool(**kwargs)


if __name__ == "__main__":
    # 簡單測試
    print("=" * 50)
    print("平行搜尋工具測試")
    print("=" * 50)

    result = parallel_search("私立揚才文理短期補習班")

    print("\n" + "=" * 50)
    print("結果")
    print("=" * 50)
    print(f"成功: {result.success}")
    print(f"工具類型: {result.tool_type}")
    print(f"耗時: {result.elapsed_time:.2f}s")
    print(f"API 呼叫: {result.api_calls}")
    print(f"信心度: {result.data.get('_confidence', 'N/A')}")
    print(f"資料內容:")
    print(json.dumps(result.data, ensure_ascii=False, indent=2))
