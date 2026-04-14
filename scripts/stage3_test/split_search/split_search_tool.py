"""
拆分查詢搜尋工具 (Split Search Tool)
======================================

目標：測試將一個查詢拆分成多個針對性查詢的效能

設計：
1. 預先定義多個欄位的查詢模板
2. 並行執行多個拆分查詢
3. 合併結果

查詢拆分策略：
- 統一編號查詢
- 成立時間查詢
- 資本額查詢
- 主要服務查詢
- 公司地址查詢
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
# scripts/stage3_test/split_search/split_search_tool.py
# 往上 4 層: split_search -> stage3_test -> scripts -> 專案根目錄
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


# ===== 搜尋結果資料類別 =====
@dataclass
class SearchResult:
    """統一搜尋結果格式"""

    success: bool
    tool_type: str
    elapsed_time: float
    api_calls: int
    data: Dict[str, Any]
    raw_answer: str
    answer_length: int


# ===== 查詢模板 =====
QUERY_TEMPLATES = {
    "unified_number": "{company} 統一編號",
    "founded_date": "{company} 成立時間 成立日期",
    "capital": "{company} 資本額",
    "main_services": "{company} 主要服務 主要產品",
    "address": "{company} 公司地址",
    "officer": "{company} 負責人 代表人",
    "business_items": "{company} 營業項目 經營項目",
}


# ===== Tavily 工具包裝 =====
class TavilySearchTool:
    """Tavily 搜尋工具"""

    tool_name = "TavilySearchTool"

    def __init__(self, **kwargs):
        from src.services.tavily_search import TavilySearchProvider

        self.max_results = kwargs.get("max_results", 2)

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key or api_key == "dummy_value":
            raise ValueError("TAVILY_API_KEY is required")

        self.provider = TavilySearchProvider(
            api_key=api_key,
            max_results=self.max_results,
            include_answer=True,
        )

    def search(self, query: str, **kwargs) -> SearchResult:
        """執行單一查詢"""
        import re

        start = time.time()
        result = self.provider.get_search_info(query, max_results=self.max_results)
        elapsed = time.time() - start

        answer = result.get("answer", "")

        return SearchResult(
            success=True,
            tool_type="tavily",
            elapsed_time=elapsed,
            api_calls=1,
            data={
                "query": query,
                "answer": answer,
                "results": result.get("results", []),
            },
            raw_answer=answer,
            answer_length=len(answer),
        )


# ===== 拆分查詢搜尋工具 =====
class SplitSearchTool:
    """
    拆分查詢搜尋工具

    設計：
    1. 將公司查詢拆分成多個針對性查詢
    2. 並行執行拆分查詢
    3. 合併結果並解析欄位
    """

    tool_name = "SplitSearchTool"

    def __init__(self, **kwargs):
        """
        初始化拆分查詢工具

        Args:
            fields: 要查詢的欄位列表，預設全部
            timeout: 總超時時間（秒）
            parallel: 是否並行執行
        """
        self.fields = kwargs.get("fields", list(QUERY_TEMPLATES.keys()))
        self.timeout = kwargs.get("timeout", 15)
        self.parallel = kwargs.get("parallel", True)

        print(f"\n🔧 SplitSearchTool 初始化")
        print(f"   查詢欄位: {self.fields}")
        print(f"   並行模式: {self.parallel}")

    def search(self, query: str, **kwargs) -> SearchResult:
        """
        執行拆分查詢

        Args:
            query: 公司名稱

        Returns:
            SearchResult: 合併後的搜尋結果
        """
        start = time.time()

        # 生成拆分查詢
        queries = []
        for field in self.fields:
            template = QUERY_TEMPLATES.get(field, "{company}")
            search_query = template.format(company=query)
            queries.append((field, search_query))

        print(f"\n📤 拆分查詢開始")
        print(f"   公司：{query}")
        print(f"   查詢數量：{len(queries)}")
        for field, q in queries:
            print(f"   - {field}: {q}")

        # 建立 Tavily 工具
        tavily = TavilySearchTool()

        # 執行查詢
        if self.parallel:
            results = self._parallel_search(queries, tavily)
        else:
            results = self._sequential_search(queries, tavily)

        elapsed = time.time() - start

        # 合併結果
        merged = self._merge_results(results)

        print(f"\n📊 拆分查詢結果")
        print(f"   總耗時: {elapsed:.2f}s")
        print(
            f"   成功查詢: {len([r for r in results if r[1].success])}/{len(queries)}"
        )
        print(f"   合併結果:")
        for field, value in merged.items():
            if not field.startswith("_"):
                print(f"     - {field}: {str(value)[:50]}...")

        return SearchResult(
            success=len([r for r in results if r[1].success]) > 0,
            tool_type="split_search",
            elapsed_time=elapsed,
            api_calls=len(queries),
            data={
                **merged,
                "_queries": len(queries),
                "_results": {field: r.elapsed_time for field, r in results},
            },
            raw_answer=str(merged),
            answer_length=len(str(merged)),
        )

    def _parallel_search(
        self, queries: List[tuple], tavily: TavilySearchTool
    ) -> List[tuple]:
        """並行執行查詢"""
        results = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(queries)
        ) as executor:
            futures = {executor.submit(tavily.search, q): field for field, q in queries}

            for future in concurrent.futures.as_completed(
                futures, timeout=self.timeout
            ):
                field = futures[future]
                try:
                    result = future.result()
                    results.append((field, result))
                    print(f"   ✅ {field} 完成，耗時 {result.elapsed_time:.2f}s")
                except Exception as e:
                    print(f"   ❌ {field} 失敗: {e}")
                    results.append(
                        (
                            field,
                            SearchResult(
                                success=False,
                                tool_type="tavily",
                                elapsed_time=0,
                                api_calls=0,
                                data={"error": str(e)},
                                raw_answer="",
                                answer_length=0,
                            ),
                        )
                    )

        return results

    def _sequential_search(
        self, queries: List[tuple], tavily: TavilySearchTool
    ) -> List[tuple]:
        """順序執行查詢"""
        results = []

        for field, query in queries:
            start = time.time()
            try:
                result = tavily.search(query)
                results.append((field, result))
                print(f"   ✅ {field} 完成，耗時 {result.elapsed_time:.2f}s")
            except Exception as e:
                print(f"   ❌ {field} 失敗: {e}")
                results.append(
                    (
                        field,
                        SearchResult(
                            success=False,
                            tool_type="tavily",
                            elapsed_time=0,
                            api_calls=0,
                            data={"error": str(e)},
                            raw_answer="",
                            answer_length=0,
                        ),
                    )
                )

        return results

    def _merge_results(self, results: List[tuple]) -> Dict[str, Any]:
        """合併結果"""
        merged = {
            "_field_count": len(results),
            "_success_count": sum(1 for _, r in results if r.success),
        }

        import re

        for field, result in results:
            if not result.success:
                continue

            answer = result.data.get("answer", "")

            # 根據欄位解析
            if field == "unified_number":
                match = re.search(r"[0-9]{8}", answer)
                merged[field] = match.group(0) if match else answer[:20]
            elif field == "founded_date":
                match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日|\d{4}年)", answer)
                merged[field] = match.group(0) if match else answer[:30]
            elif field == "capital":
                match = re.search(r"([0-9,]+[萬億]?元|[0-9,]+千元)", answer)
                merged[field] = match.group(0) if match else answer[:30]
            elif field == "address":
                match = re.search(r"([^\n。]{5,50})", answer)
                merged[field] = match.group(0) if match else answer[:50]
            else:
                merged[field] = answer[:100] if len(answer) > 100 else answer

        return merged


# ===== 便捷函式 =====
def split_search(query: str, parallel: bool = True) -> SearchResult:
    """便捷函式：執行拆分查詢"""
    tool = SplitSearchTool(parallel=parallel)
    return tool.search(query)


if __name__ == "__main__":
    # 簡單測試
    print("=" * 50)
    print("拆分查詢工具測試")
    print("=" * 50)

    # 測試並行模式
    print("\n>>> 並行模式")
    result = split_search("私立揚才文理短期補習班", parallel=True)
    print(f"\n成功: {result.success}")
    print(f"耗時: {result.elapsed_time:.2f}s")
    print(f"API 呼叫: {result.api_calls}")

    # 測試順序模式
    print("\n>>> 順序模式")
    result = split_search("私立揚才文理短期補習班", parallel=False)
    print(f"\n成功: {result.success}")
    print(f"耗時: {result.elapsed_time:.2f}s")
    print(f"API 呼叫: {result.api_calls}")
