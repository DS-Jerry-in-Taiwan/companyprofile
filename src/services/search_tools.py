"""
搜尋工具層 (Search Tools Layer)
===============================

目標：將搜尋策略抽象化成統一工具層，方便主流程透過參數調用

設計原則：
1. 註冊制：各策略工具需註冊到工廠
2. 參數化：透過參數選擇要使用的工具
3. 統一介面：所有工具都實現統一的 search() 方法

支援的策略：

| 策略 | 工具類別 | API 呼叫 | 特性 |
|------|----------|---------|------|
| tavily | TavilyBatchSearchTool | 1次 | 快速、自然語言 |
| gemini_fewshot | GeminiFewShotSearchTool | 1次 | 完整、JSON 格式 |
| gemini_planner_tavily | GeminiPlannerTavilyTool | 8次 | 彈性、結構化 |

使用範例：
```python
# 方式一：配置驅動搜尋（推薦）
from src.services.config_driven_search import search
result = search("澳霸有限公司")  # 自動根據 config/search_config.json 執行

# 方式二：直接透過工廠建立
from src.services.search_tools import SearchToolFactory, SearchToolType
tool = SearchToolFactory.create(SearchToolType.GEMINI_FEWSHOT)
result = tool.search("澳霸有限公司")

# 方式三：透過工廠並指定參數
from src.services.search_tools import create_search_tool
tool = create_search_tool("tavily", max_results=5)
result = tool.search("澳霸有限公司")
```

相關檔案：
- config_driven_search.py: 配置驅動搜尋工具
- config/search_config.json: 搜尋策略配置
"""

import os
import sys
import time
import json
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# 專案根目錄
_CURRENT_FILE = os.path.abspath(__file__)
# /home/ubuntu/projects/OrganBriefOptimization/src/services/search_tools.py
# 需要往上 3 層: services -> src -> 專案根目錄
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
from google.genai import types as genai_types

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


# ===== 工具類型枚舉 =====
class SearchToolType(Enum):
    """支援的搜尋工具類型"""

    TAVILY = "tavily"  # Tavily 批次搜尋
    TAVILY_SEQUENTIAL = "tavily_sequential"  # Tavily 逐項搜尋
    TAVILY_HYBRID = "tavily_hybrid"  # Tavily 混合模式
    GEMINI_FEWSHOT = "gemini_fewshot"  # Gemini Few-shot 搜尋
    GEMINI_PLANNER_TAVILY = "gemini_planner_tavily"  # Gemini 規劃 + Tavily 執行
    PARALLEL_MULTI_SOURCE = "parallel_multi_source"  # 平行多來源搜尋
    PARALLEL_ASPECT_SEARCH = "parallel_aspect_search"  # 平行面向搜尋
    PARALLEL_FIELD_SEARCH = "parallel_field_search"  # 平行字段搜尋


# ===== 結構化欄位定義 =====
STRUCTURED_FIELDS = {
    "unified_number": "統一編號（8位數字）",
    "capital": "資本額（新台幣）",
    "founded_date": "成立時間/日期",
    "address": "公司地址",
    "officer": "負責人/代表人",
    "main_services": "主要產品/服務",
    "business_items": "營業項目",
}


# ===== 搜尋結果資料類別 =====
@dataclass
class SearchResult:
    """統一搜尋結果格式"""

    success: bool
    tool_type: str
    elapsed_time: float
    api_calls: int
    data: Dict[str, Any]  # 結構化資料
    raw_answer: str  # 原始回答
    answer_length: int  # 回答長度

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


# ===== 抽象工具基類 =====
class BaseSearchTool(ABC):
    """
    搜尋工具抽象基類

    所有具體搜尋工具都需繼承此類並實現 search() 方法
    """

    def __init__(self, **kwargs):
        """
        初始化搜尋工具

        Args:
            **kwargs: 工具特定參數
        """
        self.config = kwargs
        self._last_metadata: Dict[str, Any] = {}

    @abstractmethod
    def search(self, query: str, **kwargs) -> SearchResult:
        """
        執行搜尋

        Args:
            query: 搜尋查詢（通常是公司名稱）
            **kwargs: 額外參數

        Returns:
            SearchResult: 統一的搜尋結果格式
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """取得最後一次搜尋的元資料"""
        return self._last_metadata

    @property
    def tool_name(self) -> str:
        """工具名稱"""
        return self.__class__.__name__


# ===== 策略一：Tavily 批次搜尋工具 =====
class TavilyBatchSearchTool(BaseSearchTool):
    """
    Tavily 批次搜尋工具

    一次問多個欄位，適合快速取得基本資訊
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from src.services.tavily_search import TavilySearchProvider

        self.max_results = kwargs.get("max_results", 3)
        self.include_answer = kwargs.get("include_answer", True)

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key or api_key == "dummy_value":
            raise ValueError("TAVILY_API_KEY is required")

        self.provider = TavilySearchProvider(
            api_key=api_key,
            max_results=self.max_results,
            include_answer=self.include_answer,
        )

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行批次搜尋"""
        max_results = kwargs.get("max_results", self.max_results)

        # 組合成一個大 query
        fields_query = "、".join(STRUCTURED_FIELDS.values())
        full_query = f"{query} 的 {fields_query}"

        start = time.time()
        result = self.provider.get_search_info(full_query, max_results=max_results)
        elapsed = time.time() - start

        answer = result.get("answer", "")

        # 簡單解析欄位
        data = self._parse_fields(answer)

        self._last_metadata = {
            "query": full_query,
            "total_results": len(result.get("results", [])),
            "response_time": result.get("response_time", 0),
        }

        return SearchResult(
            success=True,
            tool_type=SearchToolType.TAVILY.value,
            elapsed_time=elapsed,
            api_calls=1,
            data=data,
            raw_answer=answer,
            answer_length=len(answer),
        )

    def _parse_fields(self, answer: str) -> Dict[str, str]:
        """簡單解析欄位"""
        data = {}
        for field_key, field_name in STRUCTURED_FIELDS.items():
            if field_key == "unified_number" and (
                "統一編號" in answer or any(c.isdigit() for c in answer[:100])
            ):
                match = re.search(r"[0-9]{8}", answer)
                data[field_key] = match.group(0) if match else "不詳"
            elif field_key == "capital" and "資本" in answer:
                match = re.search(r"[0-9,]+[萬億]?[元]", answer)
                data[field_key] = match.group(0) if match else answer[:30]
            elif field_key == "address" and ("市" in answer or "區" in answer):
                match = re.search(r"[^\n。]{5,40}", answer)
                data[field_key] = match.group(0) if match else answer[:40]
            else:
                data[field_key] = answer[:50] if len(answer) > 50 else answer
        return data


# ===== 策略二：Gemini Few-shot 搜尋工具 =====
class GeminiFewShotSearchTool(BaseSearchTool):
    """
    Gemini Few-shot 搜尋工具

    使用 Gemini 的 Google Search 功能，直接取得結構化 JSON
    資訊最完整，但速度稍慢
    """

    # 具體字段 Prompt（使用 Google Search + JSON）
    GEMINI_PROMPT_TEMPLATE = """你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊。

【搜尋任務】
請使用 Google Search 搜尋並提取以下具體字段資訊：

1. 統一編號：公司的統一編號（8位數字）
2. 資本額：公司的資本額（新台幣）
3. 成立時間：公司的成立時間或日期
4. 公司地址：公司的登記地址
5. 負責人：公司的負責人或代表人
6. 主要產品服務：公司的主要產品或服務
7. 營業項目：公司的營業項目

【輸出格式】
請用 JSON 格式回覆，格式如下：
{{"unified_number": "值", "capital": "值", "founded_date": "值", "address": "值", "officer": "值", "main_services": "值", "business_items": "值"}}

【嚴格要求】
- 只使用實際搜尋到的資訊，絕對不要編造或推測
- 如果某字段找不到相關資訊，使用 "未找到"
- 絕對不要用 xxx 或任何占位符
- 使用專業、客觀的語言
- 用繁體中文回答
- 只回覆 JSON，不要有其他內容"""

    # Structured Output Schema - 具體字段格式
    RESPONSE_SCHEMA = genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={
            "unified_number": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="統一編號：公司的統一編號（8位數字）",
            ),
            "capital": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="資本額：公司的資本額（新台幣）",
            ),
            "founded_date": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="成立時間：公司的成立時間或日期",
            ),
            "address": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="公司地址：公司的登記地址",
            ),
            "officer": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="負責人：公司的負責人或代表人",
            ),
            "main_services": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="主要產品/服務：公司的主要產品或服務",
            ),
            "business_items": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="營業項目：公司的營業項目",
            ),
        },
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from google import genai

        self.model = kwargs.get("model", "gemini-2.0-flash")
        self.temperature = kwargs.get("temperature", 0.2)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self.search_tool = genai_types.Tool(google_search=genai_types.GoogleSearch())

    def _get_structured_config(self) -> "genai_types.GenerateContentConfig":
        """取得 Config - 使用 Google Search"""
        return genai_types.GenerateContentConfig(
            tools=[self.search_tool],  # 配置 Google Search
        )

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行 Gemini Few-shot 搜尋"""
        prompt = self.GEMINI_PROMPT_TEMPLATE.format(company_name=query)

        start = time.time()
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._get_structured_config(),
        )
        elapsed = time.time() - start

        raw_answer = response.text

        # 解析 JSON
        try:
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw_answer, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = {"raw": raw_answer}
        except json.JSONDecodeError:
            data = {"raw": raw_answer}
            data = {"raw": raw_answer[:500]}

        self._last_metadata = {
            "query": query,
            "model": self.model,
            "json_parsed": True,
        }

        return SearchResult(
            success=True,
            tool_type=SearchToolType.GEMINI_FEWSHOT.value,
            elapsed_time=elapsed,
            api_calls=1,
            data=data,
            raw_answer=raw_answer,
            answer_length=len(raw_answer),
        )


# ===== 策略三：Gemini 規劃 + Tavily 執行工具 =====
class GeminiPlannerTavilyTool(BaseSearchTool):
    """
    Gemini 規劃 + Tavily 執行工具

    概念：
    1. Gemini 產出結構化查詢框架
    2. 用 Tavily 批次查詢各欄位
    3. 合併結果

    優點：
    - Gemini：聰明的規劃者
    - Tavily：便宜的執行者
    """

    GEMINI_PLANNER_PROMPT = """你是一個公司資訊搜尋規劃專家。

任務：為「{company_name}」規劃搜尋框架。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "{company_name}",
    "queries": [
        {{
            "field": "面向名稱",
            "query": "Tavily 搜尋查詢",
            "priority": 1-3（1最高）,
            "description": "為什麼要查這個"
        }}
    ],
    "confidence": "高/中/低"
}}

【面向定義】
- foundation: 品牌實力與基本資料
- core: 技術產品與服務核心
- vibe: 職場環境與企業文化
- future: 近期動態與未來展望

【查詢規則】
1. 根據公司名稱，規劃最適合的搜尋關鍵字
2. 每個面向規劃 2-3 個查詢
3. 優先查最重要的資訊
4. 每個查詢要具體明確

請回覆 JSON："""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from google import genai
        from google.genai import types
        from src.services.tavily_search import TavilySearchProvider

        self.max_results = kwargs.get("max_results", 2)
        self.model = kwargs.get("model", "gemini-2.0-flash")
        self.temperature = kwargs.get("temperature", 0.1)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.gemini_client = genai.Client(api_key=api_key)
        self._types = types  # 保存引用
        self.search_tool = types.Tool(google_search=types.GoogleSearch())

        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key or tavily_key == "dummy_value":
            raise ValueError("TAVILY_API_KEY is required")

        self.tavily_provider = TavilySearchProvider(api_key=tavily_key)

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行 Gemini 規劃 + Tavily 執行"""
        # Step 1: Gemini 規劃
        planner_prompt = self.GEMINI_PLANNER_PROMPT.format(company_name=query)

        start = time.time()
        planner_response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=planner_prompt,
            config=self._types.GenerateContentConfig(
                tools=[self.search_tool],
                temperature=self.temperature,
            ),
        )
        planner_time = time.time() - start

        # 解析 JSON
        json_match = re.search(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", planner_response.text, re.DOTALL
        )

        if not json_match:
            return SearchResult(
                success=False,
                tool_type=SearchToolType.GEMINI_PLANNER_TAVILY.value,
                elapsed_time=time.time() - start,
                api_calls=1,
                data={},
                raw_answer=planner_response.text,
                answer_length=len(planner_response.text),
            )

        try:
            query_framework = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return SearchResult(
                success=False,
                tool_type=SearchToolType.GEMINI_PLANNER_TAVILY.value,
                elapsed_time=time.time() - start,
                api_calls=1,
                data={},
                raw_answer=planner_response.text,
                answer_length=len(planner_response.text),
            )

        # Step 2: Tavily 批次執行
        queries = query_framework.get("queries", [])
        search_results = {}
        search_start = time.time()

        for q in queries:
            field = q["field"]
            search_query = q["query"]

            result = self.tavily_provider.get_search_info(
                search_query, max_results=self.max_results
            )
            search_results[field] = {
                "answer": result.get("answer", ""),
                "raw_results": result.get("results", []),
            }

        search_time = time.time() - search_start
        total_time = planner_time + search_time

        # Step 3: 合併結果
        merged = self._merge_results(queries, search_results)

        self._last_metadata = {
            "query_framework": query_framework,
            "search_results": search_results,
            "api_calls": 1 + len(queries),
        }

        return SearchResult(
            success=True,
            tool_type=SearchToolType.GEMINI_PLANNER_TAVILY.value,
            elapsed_time=total_time,
            api_calls=1 + len(queries),
            data=merged,
            raw_answer=json.dumps(merged, ensure_ascii=False),
            answer_length=sum(len(str(v)) for v in merged.values()),
        )

    def _merge_results(
        self, queries: List[Dict], search_results: Dict[str, Any]
    ) -> Dict[str, str]:
        """合併搜尋結果為結構化資料（按四面向）"""
        merged = {}

        for q in queries:
            field = q["field"]
            answer = search_results.get(field, {}).get("answer", "")

            # 按面向合併多個查詢結果
            if field in merged:
                merged[field] += "\n" + answer  # 相同面向追加
            else:
                merged[field] = answer

        return merged


# ===== 平行多來源搜尋工具 =====
class ParallelMultiSourceTool(BaseSearchTool):
    """
    平行多來源搜尋工具

    設計：
    1. 同時執行多個搜尋工具（Tavily + Gemini）
    2. 取所有結果 + 多源交叉驗證
    3. 回傳信心度指標

    使用方式：
    ```python
    from src.services.search_tools import create_search_tool

    tool = create_search_tool("parallel_multi_source", sources=["tavily", "gemini_fewshot"])
    result = tool.search("公司名稱")
    ```
    """

    def __init__(self, **kwargs):
        """
        初始化平行搜尋工具

        Args:
            sources: 要平行執行的工具列表，預設 ["tavily", "gemini_fewshot"]
            timeout: 總超時時間（秒），預設 15
        """
        super().__init__(**kwargs)

        self.sources = kwargs.get("sources", ["tavily", "gemini_fewshot"])
        self.timeout = kwargs.get("timeout", 15)
        self.confidence_threshold = kwargs.get("confidence_threshold", 0.6)

        import logging

        self.logger = logging.getLogger(__name__)

    def search(self, query: str, **kwargs) -> SearchResult:
        """
        執行平行搜尋

        Args:
            query: 搜尋查詢（公司名稱）
            **kwargs: 額外參數

        Returns:
            SearchResult: 合併後的搜尋結果
        """
        import concurrent.futures
        import time

        start = time.time()

        # 建立工具
        tools = []
        for source in self.sources:
            if source == "tavily":
                tools.append(("tavily", TavilyBatchSearchTool()))
            elif source == "gemini_fewshot":
                tools.append(("gemini_fewshot", GeminiFewShotSearchTool()))

        self.logger.info(f"[PARALLEL] 平行搜尋開始，工具數量: {len(tools)}")

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
                    self.logger.info(
                        f"[PARALLEL] {name} 完成，耗時 {result.elapsed_time:.2f}s"
                    )
                except Exception as e:
                    errors.append({"source": name, "error": str(e)})
                    self.logger.warning(f"[PARALLEL] {name} 失敗: {e}")

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

        self.logger.info(
            f"[PARALLEL] 完成，總耗時: {elapsed:.2f}s，"
            f"成功: {len(results)}/{len(tools)}，信心度: {confidence}"
        )

        return SearchResult(
            success=len(results) > 0,
            tool_type=SearchToolType.PARALLEL_MULTI_SOURCE.value,
            elapsed_time=elapsed,
            api_calls=sum(r.api_calls for r in results),
            data={**merged_data, **metadata},
            raw_answer=str(merged_data),
            answer_length=len(str(merged_data)),
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
                        # 發現差異，標記交叉驗證
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


# ===== 策略六：平行面向搜尋工具 =====
class ParallelAspectSearchTool(BaseSearchTool):
    """
    平行面向搜尋工具

    設計：
    1. 為每個面向建立獨立的 prompt
    2. 同時發送多個 LLM API 請求
    3. 等待所有請求完成
    4. 彙整所有結果

    優點：
    - 真正的平行處理
    - 每個面向專注查詢
    - 可擴展到多個 LLM
    """

    # 4 個面向的獨立 Prompt（使用 Structured Output，無需強調 JSON 格式）
    ASPECT_PROMPTS = {
        "foundation": """你是一個公司資訊搜尋專家。請搜尋「{company}」的品牌實力與基本資料，包括成立時間、統一編號、資本額、規模、主要投資方、獲獎榮譽等。

重要：只使用實際搜尋到的資訊。如果找不到相關資訊，回覆：「該面向的相關資訊暫時無法獲取。」絕對不要生成「請根據實際情況填寫」這類模板文字。""",
        "core": """你是一個公司資訊搜尋專家。請搜尋「{company}」的技術產品與服務核心，包括主要產品、技術亮點、服務內容、核心競爭力、市場定位、產業地位等。

重要：只使用實際搜尋到的資訊。如果找不到相關資訊，回覆：「該面向的相關資訊暫時無法獲取。」絕對不要生成「請根據實際情況填寫」這類模板文字。""",
        "vibe": """你是一個公司資訊搜尋專家。請搜尋「{company}」的職場環境與企業文化，包括員工評價、工作氛圍、企業文化、團隊特色、福利制度、ESG表現等。

重要：只使用實際搜尋到的資訊。如果找不到相關資訊，回覆：「該面向的相關資訊暫時無法獲取。」絕對不要生成「請根據實際情況填寫」這類模板文字。""",
        "future": """你是一個公司資訊搜尋專家。請搜尋「{company}」的近期動態與未來展望，包括最新新聞、發展計劃、投資動向、市場前景、擴張計畫、策略方向等。

重要：只使用實際搜尋到的資訊。如果找不到相關資訊，回覆：「該面向的相關資訊暫時無法獲取。」絕對不要生成「請根據實際情況填寫」這類模板文字。""",
    }

    # Structured Output Schema - 確保輸出格式一致
    RESPONSE_SCHEMA = genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={
            "foundation": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="品牌實力與基本資料：公司名稱、成立時間、統一編號、資本額、規模、主要投資方、獲獎榮譽等。不超過500字。",
            ),
            "core": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="技術產品與服務核心：主要產品、技術亮點、服務內容、核心競爭力、市場定位、產業地位等。不超過500字。",
            ),
            "vibe": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="職場環境與企業文化：員工評價、工作氛圍、企業文化、團隊特色、福利制度、ESG表現等。不超過500字。",
            ),
            "future": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="近期動態與未來展望：最新新聞、發展計劃、投資動向、市場前景、擴張計畫、策略方向等。不超過500字。",
            ),
        },
        required=["foundation", "core", "vibe", "future"],
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from google import genai

        self.model = kwargs.get("model", "gemini-2.0-flash")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_workers = kwargs.get("max_workers", 4)
        self.timeout = kwargs.get("timeout", 15)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self.search_tool = genai_types.Tool(google_search=genai_types.GoogleSearch())

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行平行面向搜尋"""
        import concurrent.futures

        start_time = time.time()

        # 1. 建立 4 個面向的查詢任務
        tasks = []
        for aspect, prompt_template in self.ASPECT_PROMPTS.items():
            prompt = prompt_template.format(company=query)
            tasks.append((aspect, prompt))

        # 2. 平行執行所有查詢
        results = {}
        errors = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # 提交所有任務
            future_to_aspect = {
                executor.submit(self._search_single_aspect, aspect, prompt): aspect
                for aspect, prompt in tasks
            }

            # 收集結果
            for future in concurrent.futures.as_completed(
                future_to_aspect, timeout=self.timeout
            ):
                aspect = future_to_aspect[future]
                try:
                    result = future.result()
                    results[aspect] = result
                except Exception as e:
                    errors[aspect] = str(e)

        elapsed_time = time.time() - start_time

        # 3. 彙整結果
        merged_data = {
            aspect: result.get("content", "") for aspect, result in results.items()
        }

        # 4. 建立 SearchResult
        return SearchResult(
            success=len(results) > 0,
            tool_type="parallel_aspect_search",
            elapsed_time=elapsed_time,
            api_calls=len(tasks),
            data=merged_data,
            raw_answer=json.dumps(merged_data, ensure_ascii=False),
            answer_length=sum(len(str(v)) for v in merged_data.values()),
        )

    def _get_structured_config(self) -> "genai_types.GenerateContentConfig":
        """取得 Structured Output Config"""
        return genai_types.GenerateContentConfig(
            response_schema=self.RESPONSE_SCHEMA,
            response_mime_type="application/json",
        )

    def _search_single_aspect(self, aspect: str, prompt: str) -> Dict:
        """搜尋單個面向 - 使用 Structured Output"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self._get_structured_config(),
            )

            # 直接解析 JSON（因為已經強制 JSON 格式）
            data = json.loads(response.text)

            return {
                "aspect": aspect,
                "content": data.get(aspect, ""),  # 一定是字串
                "success": True,
            }
        except Exception as e:
            return {
                "aspect": aspect,
                "content": "",
                "success": False,
                "error": str(e),
            }


# ===== 策略七：平行字段搜尋工具 =====
class ParallelFieldSearchTool(BaseSearchTool):
    """
    平行字段搜尋工具

    設計：
    1. 為每個具體字段建立獨立的 prompt
    2. 同時發送多個 LLM API 請求（使用 Google Search 工具）
    3. 等待所有請求完成
    4. 彙整所有結果並添加防呆標記

    優點：
    - 具體字段格式，容易搜尋
    - 明確配置 Google Search 工具
    - 平行處理提高速度
    - 防呆機制避免編造
    """

    # 7 個具體字段的獨立 Prompt
    FIELD_PROMPTS = {
        "unified_number": """請搜尋「{company}」的統一編號（8位數字）。
        
重要：只使用實際搜尋到的資訊。如果找不到，回覆：「未找到」。絕對不要編造或推測。""",
        "capital": """請搜尋「{company}」的資本額（新台幣），例如「500萬元」、「1000萬元」等。
        
重要：只使用實際搜尋到的資訊。如果找不到，回覆：「未找到」。絕對不要編造或推測。""",
        "founded_date": """請搜尋「{company}」的成立時間/日期。
        
重要：只使用實際搜尋到的資訊。如果找不到，回覆：「未找到」。絕對不要編造或推測。""",
        "address": """請搜尋「{company}」的公司地址。
        
重要：只使用實際搜尋到的資訊。如果找不到，回覆：「未找到」。絕對不要編造或推測。""",
        "officer": """請搜尋「{company}」的負責人/代表人。
        
重要：只使用實際搜尋到的資訊。如果找不到，回覆：「未找到」。絕對不要編造或推測。""",
        "main_services": """請搜尋「{company}」的主要產品/服務。
        
重要：只使用實際搜尋到的資訊。如果找不到，回覆：「未找到」。絕對不要編造或推測。""",
        "business_items": """請搜尋「{company}」的營業項目。
        
重要：只使用實際搜尋到的資訊。如果找不到，回覆：「未找到」。絕對不要編造或推測。""",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from google import genai

        self.model = kwargs.get("model", "gemini-2.0-flash")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_workers = kwargs.get("max_workers", 7)  # 7 個字段
        self.timeout = kwargs.get("timeout", 20)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self.search_tool = genai_types.Tool(google_search=genai_types.GoogleSearch())

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行平行字段搜尋"""
        import concurrent.futures

        start_time = time.time()

        # 1. 建立 7 個字段的查詢任務
        tasks = []
        for field, prompt_template in self.FIELD_PROMPTS.items():
            prompt = prompt_template.format(company=query)
            tasks.append((field, prompt))

        # 2. 平行執行所有查詢
        results = {}
        errors = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # 提交所有任務
            future_to_field = {
                executor.submit(self._search_single_field, field, prompt): field
                for field, prompt in tasks
            }

            # 收集結果
            for future in concurrent.futures.as_completed(
                future_to_field, timeout=self.timeout
            ):
                field = future_to_field[future]
                try:
                    result = future.result()
                    results[field] = result
                except Exception as e:
                    errors[field] = str(e)

        elapsed_time = time.time() - start_time

        # 3. 彙整結果並添加防呆標記
        merged_data = self._merge_results(results)
        
        # 4. 計算統計資訊
        found_fields = sum(1 for v in merged_data.values() if v != "未找到" and v != "")
        total_fields = len(merged_data)
        
        # 添加 metadata
        merged_data["_metadata"] = {
            "missing_fields": [k for k, v in merged_data.items() if v == "未找到" or v == ""],
            "found_fields": found_fields,
            "total_fields": total_fields,
            "search_time": elapsed_time,
            "errors": errors if errors else None,
        }

        # 5. 建立 SearchResult
        return SearchResult(
            success=found_fields > 0,  # 至少找到一個字段就算成功
            tool_type="parallel_field_search",
            elapsed_time=elapsed_time,
            api_calls=len(tasks),
            data=merged_data,
            raw_answer=json.dumps(merged_data, ensure_ascii=False),
            answer_length=sum(len(str(v)) for v in merged_data.values() if not isinstance(v, dict)),
        )

    def _search_single_field(self, field: str, prompt: str) -> Dict:
        """搜尋單個字段 - 使用 Google Search 工具"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    tools=[self.search_tool],  # 關鍵：啟用 Google Search
                    temperature=self.temperature,
                ),
            )

            content = response.text.strip()
            
            # 檢查是否為「未找到」
            if content == "未找到" or "找不到" in content or "無法獲取" in content:
                return {
                    "field": field,
                    "content": "未找到",
                    "success": False,
                    "reason": "no_data_found",
                }
            
            return {
                "field": field,
                "content": content,
                "success": True,
            }
        except Exception as e:
            return {
                "field": field,
                "content": "",
                "success": False,
                "error": str(e),
            }

    def _merge_results(self, results: Dict[str, Dict]) -> Dict[str, str]:
        """合併搜尋結果並清理格式"""
        merged = {}
        for field, result in results.items():
            if result.get("success", False):
                content = result.get("content", "")
                # 清理格式：提取關鍵數據
                cleaned = self._clean_field_content(field, content)
                merged[field] = cleaned
            else:
                merged[field] = "未找到"
        return merged
    
    def _clean_field_content(self, field: str, content: str) -> str:
        """清理字段內容，提取關鍵數據"""
        content = content.strip()
        
        # 移除常見的開頭語句
        patterns_to_remove = [
            f"{field}是",
            f"{field}為",
            f"{field}：",
            f"{field}:",
            "根據搜尋結果，",
            "搜尋結果顯示，",
            "澳霸有限公司的",
            "的統一編號是",
            "的負責人/代表人是",
            "成立於",
            "主要從事以下產品/服務：",
            "的營業項目包括：",
        ]
        
        for pattern in patterns_to_remove:
            if content.startswith(pattern):
                content = content[len(pattern):].strip()
        
        # 特殊處理每個字段
        if field == "unified_number":
            # 提取數字
            import re
            match = re.search(r"[0-9]{8}", content)
            if match:
                return match.group(0)
        
        elif field == "capital":
            # 提取資本額數字
            import re
            # 匹配「500萬元」、「1000萬元」等格式
            match = re.search(r"[0-9,]+[萬億]?元", content)
            if match:
                return match.group(0)
        
        elif field == "founded_date":
            # 提取日期
            import re
            # 匹配「2018年6月5日」等格式
            match = re.search(r"[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日", content)
            if match:
                return match.group(0)
        
        elif field == "address":
            # 取第一個地址
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("*") and "市" in line and "區" in line:
                    return line
        
        elif field == "officer":
            # 移除句點
            if content.endswith("."):
                content = content[:-1]
        
        return content


# ===== 工具工廠 =====
class SearchToolFactory:
    """
    搜尋工具工廠

    負責註冊和創建各種搜尋工具

    使用方式：
    ```python
    # 創建工具
    tool = SearchToolFactory.create(SearchToolType.GEMINI_FEWSHOT)

    # 執行搜尋
    result = tool.search("澳霸有限公司")
    ```
    """

    # 工具註冊表
    _registry: Dict[SearchToolType, type] = {
        SearchToolType.TAVILY: TavilyBatchSearchTool,
        SearchToolType.TAVILY_SEQUENTIAL: TavilyBatchSearchTool,  # 暫用同一個
        SearchToolType.TAVILY_HYBRID: TavilyBatchSearchTool,  # 暫用同一個
        SearchToolType.GEMINI_FEWSHOT: GeminiFewShotSearchTool,
        SearchToolType.GEMINI_PLANNER_TAVILY: GeminiPlannerTavilyTool,
        SearchToolType.PARALLEL_MULTI_SOURCE: ParallelMultiSourceTool,
        SearchToolType.PARALLEL_ASPECT_SEARCH: ParallelAspectSearchTool,
        SearchToolType.PARALLEL_FIELD_SEARCH: ParallelFieldSearchTool,
    }

    @classmethod
    def register(cls, tool_type: SearchToolType, tool_class: type):
        """註冊新的搜尋工具"""
        if not issubclass(tool_class, BaseSearchTool):
            raise ValueError(f"{tool_class} must be a subclass of BaseSearchTool")
        cls._registry[tool_type] = tool_class

    @classmethod
    def create(cls, tool_type: SearchToolType, **kwargs) -> BaseSearchTool:
        """
        創建搜尋工具實例

        Args:
            tool_type: 工具類型
            **kwargs: 傳給工具構造函數的參數

        Returns:
            BaseSearchTool: 搜尋工具實例
        """
        if tool_type not in cls._registry:
            raise ValueError(f"Unknown tool type: {tool_type}")

        tool_class = cls._registry[tool_type]
        return tool_class(**kwargs)

    @classmethod
    def list_tools(cls) -> List[str]:
        """列出所有已註冊的工具"""
        return [t.value for t in cls._registry.keys()]


# ===== 便捷函式 =====
def create_search_tool(tool_type: str = "gemini_fewshot", **kwargs) -> BaseSearchTool:
    """
    便捷函式：創建搜尋工具

    Args:
        tool_type: 工具類型字串 ("tavily", "gemini_fewshot", 等)
        **kwargs: 工具構造參數

    Returns:
        BaseSearchTool: 搜尋工具實例
    """
    # 轉換字串到枚舉
    tool_type_enum = None
    for t in SearchToolType:
        if t.value == tool_type.lower():
            tool_type_enum = t
            break

    if tool_type_enum is None:
        raise ValueError(f"Unknown tool type: {tool_type}")

    return SearchToolFactory.create(tool_type_enum, **kwargs)


def search_with_tool(
    query: str, tool_type: str = "gemini_fewshot", **kwargs
) -> SearchResult:
    """
    便捷函式：一步完成搜尋

    Args:
        query: 搜尋查詢
        tool_type: 工具類型
        **kwargs: 工具構造參數

    Returns:
        SearchResult: 搜尋結果
    """
    tool = create_search_tool(tool_type, **kwargs)
    return tool.search(query)
