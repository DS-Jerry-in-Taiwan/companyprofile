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

    GEMINI_PROMPT_TEMPLATE = """你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊，並以結構化 JSON 格式返回。

【核心任務】
根據搜尋結果，提取公司的四個面向的資訊，並以 JSON 格式輸出。

【輸出格式】
嚴格按以下 JSON 格式輸出（無須額外說明文本）：

```json
{{
  "foundation": "品牌實力與基本資料（不超過 500 字）",
  "core": "技術產品與服務核心（不超過 500 字）",
  "vibe": "職場環境與企業文化（不超過 500 字）",
  "future": "近期動態與未來展望（不超過 500 字）"
}}
```

【特別要求】

1. 信息準確性
   - 只使用實際搜尋到的資訊，不要編造或推測
   - 優先使用最新的資訊（偏好最近 12 個月）
   - 官方渠道信息優先於媒體報導

2. 字數控制
   - 每個面向嚴格控制在 500 字以內
   - 去除冗餘表達，保持簡潔
   - 優先保留最核心、最有價值的信息

3. 去重和合併
   - 同一個面向內的相同信息，只保留一次
   - 不同版本的信息，優先採用最新的、最權威的版本
   - 跨面向的邊界信息，分配到更相關的面向

4. 無法獲得的信息
   - 如果某個面向找不到相關信息，返回：「【暫無相關資訊】該面向的相關資訊暫時無法獲取。」
   - 不能留空或省略，保持結構完整

5. 語言和風格
   - 使用專業、客觀的語言，避免主觀評價
   - 使用現在時態描述企業情況
   - 使用具體數字和事實，而非模糊描述

【輸出檢查清單】
- [ ] 返回有效的 JSON（可被 Python `json.loads()` 解析）
- [ ] 包含四個鍵：foundation、core、vibe、future
- [ ] 每個值都是字符串類型
- [ ] 每個值都不超過 500 字
- [ ] 無編造信息，全部基於搜尋結果
- [ ] JSON 前後無額外文本說明"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from google import genai
        from google.genai import types

        self.model = kwargs.get("model", "gemini-2.0-flash")
        self.temperature = kwargs.get("temperature", 0.2)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self._types = types  # 保存引用
        self.search_tool = types.Tool(google_search=types.GoogleSearch())

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行 Gemini Few-shot 搜尋"""
        prompt = self.GEMINI_PROMPT_TEMPLATE.format(company_name=query)

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

        self._last_metadata = {
            "query": query,
            "model": self.model,
            "json_parsed": bool(json_match),
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
