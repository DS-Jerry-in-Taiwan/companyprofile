# 優化實施指南 - 分階段行動計畫

## 快速概覽

你的項目面臨 4 大問題，通過 5 個 Phase 的優化可以顯著改善。本指南提供逐步實施的具體代碼示例和檢查清單。

---

## Phase 1：改進檢索層 (1-2 週)

### 1.1 實現查詢重寫引擎

#### Step 1：創建查詢重寫模塊

**新文件：** `src/services/query_rewriter.py`

```python
"""
查詢重寫模塊 - 使用 LLM 生成多個查詢變異
用於提升搜尋覆蓋率和準確度
"""

import logging
from typing import List
from langchain.llms import ChatAnthropic  # 或你使用的 LLM

logger = logging.getLogger(__name__)


class QueryRewriter:
    def __init__(self, llm=None):
        """初始化查詢重寫器"""
        self.llm = llm or ChatAnthropic(
            api_key="your_api_key",
            model="claude-3-haiku"
        )
    
    def rewrite_queries(self, company_name: str, context: dict = None) -> List[str]:
        """
        生成多個查詢變異
        
        Args:
            company_name: 公司名稱
            context: 額外上下文（統一編號、行業等）
        
        Returns:
            查詢列表，包含原始和變異查詢
        """
        prompt = self._build_rewrite_prompt(company_name, context)
        
        response = self.llm.invoke(prompt)
        
        # 解析 LLM 回應，提取查詢列表
        queries = self._parse_queries(response.content)
        
        return queries
    
    def _build_rewrite_prompt(self, company_name: str, context: dict) -> str:
        """構建查詢重寫 Prompt"""
        
        context_str = ""
        if context:
            if context.get("organ_no"):
                context_str += f"統一編號：{context['organ_no']}\n"
            if context.get("industry"):
                context_str += f"行業：{context['industry']}\n"
            if context.get("products"):
                context_str += f"主要產品：{context['products']}\n"
        
        return f"""
你是一個搜尋策略優化專家。給定公司名稱，生成 5 個最有效的搜尋查詢。

公司名稱：{company_name}
{context_str}

要求：
1. 包含多種搜尋策略（官網搜尋、公司信息搜尋、產品搜尋等）
2. 使用不同的詞序和表述方式
3. 包含相關同義詞
4. 每個查詢應能找到不同的相關信息

輸出格式（JSON 數組）：
[
  "查詢 1",
  "查詢 2",
  "查詢 3",
  "查詢 4",
  "查詢 5"
]
"""
    
    def _parse_queries(self, response_text: str) -> List[str]:
        """解析 LLM 回應中的查詢列表"""
        import json
        import re
        
        try:
            # 嘗試直接解析 JSON
            match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if match:
                queries = json.loads(match.group())
                return queries
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback：按行分割
        lines = response_text.split('\n')
        queries = [
            line.strip().strip('"').strip("'").strip('- ')
            for line in lines
            if line.strip() and not line.startswith('[')
        ]
        return [q for q in queries if q][:5]


# 使用示例
if __name__ == "__main__":
    rewriter = QueryRewriter()
    
    queries = rewriter.rewrite_queries(
        company_name="台灣AI新創公司",
        context={
            "organ_no": "12345678",
            "industry": "人工智能",
            "products": "自然語言處理"
        }
    )
    
    print("生成的查詢：")
    for i, q in enumerate(queries, 1):
        print(f"{i}. {q}")
```

#### Step 2：整合到現有流程

**修改文件：** `src/functions/utils/generate_brief.py`

在 `_generate_brief_traditional` 函數開頭新增：

```python
# 新增：多維度查詢
from ..services.query_rewriter import QueryRewriter

def _generate_brief_traditional(data):
    organ = data["organ"]
    organ_no = data.get("organNo")
    
    # 新增：使用查詢重寫引擎生成多個查詢
    rewriter = QueryRewriter()
    queries = rewriter.rewrite_queries(
        company_name=organ,
        context={
            "organ_no": organ_no,
            "products": data.get("products", "")
        }
    )
    
    logger.info(f"生成的搜尋查詢：{queries}")
    
    # 執行並行搜尋...（後面實施）
```

#### 檢查清單：Phase 1.1
- [ ] 建立 `src/services/query_rewriter.py`
- [ ] 集成 LLM（Claude 或 Gemini）
- [ ] 在 `generate_brief.py` 中呼叫查詢重寫器
- [ ] 測試查詢生成效果
- [ ] 運行現有測試確保無迴歸

---

### 1.2 實現並行多源搜尋

#### Step 1：建立搜尋結果聚合模塊

**新文件：** `src/services/multi_source_search.py`

```python
"""
多源搜尋服務 - 並行使用多個搜尋引擎
聚合和排序結果
"""

import logging
import asyncio
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class MultiSourceSearch:
    """多源並行搜尋"""
    
    def __init__(self, max_workers=6):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def parallel_search(self, queries: List[str]) -> List[Dict]:
        """
        並行使用多個搜尋源搜尋
        
        Args:
            queries: 搜尋查詢列表
        
        Returns:
            聚合的搜尋結果列表
        """
        futures = []
        results = []
        
        # 為每個查詢分配不同的搜尋源
        for query in queries:
            # Tavily
            future_tavily = self.executor.submit(
                self._search_tavily, query
            )
            futures.append(('tavily', future_tavily))
            
            # Serper
            future_serper = self.executor.submit(
                self._search_serper, query
            )
            futures.append(('serper', future_serper))
        
        # 收集結果
        for source, future in futures:
            try:
                result = future.result(timeout=10)
                if result:
                    result['source'] = source
                    results.append(result)
            except Exception as e:
                logger.warning(f"搜尋失敗 ({source}): {str(e)}")
        
        # 聚合結果
        aggregated = self._aggregate_results(results)
        
        # 排序結果
        ranked = self._rerank_results(aggregated)
        
        return ranked
    
    def _search_tavily(self, query: str) -> Dict:
        """使用 Tavily 搜尋"""
        from .tavily_client import get_tavily_client
        
        try:
            client = get_tavily_client()
            result = client.search_and_extract(query=query, max_results=3)
            return result
        except Exception as e:
            logger.error(f"Tavily 搜尋失敗: {str(e)}")
            return None
    
    def _search_serper(self, query: str) -> Dict:
        """使用 Serper 搜尋"""
        from .serper_search import SerperSearchProvider
        import os
        
        try:
            api_key = os.getenv("SERPER_API_KEY")
            provider = SerperSearchProvider(api_key=api_key)
            results = provider.search(query, max_results=3)
            
            return {
                "success": True,
                "results": [
                    {
                        "url": r.url,
                        "title": r.title,
                        "snippet": r.snippet
                    }
                    for r in results
                ]
            }
        except Exception as e:
            logger.error(f"Serper 搜尋失敗: {str(e)}")
            return None
    
    def _aggregate_results(self, results: List[Dict]) -> List[Dict]:
        """聚合多個來源的搜尋結果"""
        aggregated = {}
        
        for result in results:
            if not result:
                continue
            
            items = result.get('results', [])
            for item in items:
                url = item.get('url', '')
                if url:
                    if url not in aggregated:
                        aggregated[url] = {
                            'url': url,
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'sources': [],
                            'relevance_score': 0
                        }
                    aggregated[url]['sources'].append(result.get('source', 'unknown'))
        
        # 轉換為列表並去重
        return list(aggregated.values())
    
    def _rerank_results(self, results: List[Dict]) -> List[Dict]:
        """
        使用 cross-encoder 重排結果
        目前採用簡單啟發式算法，後期可升級為 cross-encoder
        """
        # 基於出現在多個來源中的結果排序
        ranked = sorted(
            results,
            key=lambda x: len(x.get('sources', [])),
            reverse=True
        )
        
        return ranked[:5]  # 返回前 5 個


# 使用示例
if __name__ == "__main__":
    search = MultiSourceSearch()
    
    queries = [
        "台灣AI新創公司 官網",
        "台灣AI新創公司 公司介紹"
    ]
    
    results = search.parallel_search(queries)
    
    print("搜尋結果：")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   URL: {r['url']}")
        print(f"   來源: {', '.join(r['sources'])}\n")
```

#### Step 2：整合到生成流程

**修改文件：** `src/functions/utils/generate_brief.py`

```python
def _generate_brief_traditional(data):
    organ = data["organ"]
    organ_no = data.get("organNo")
    
    # Step 1：查詢重寫
    rewriter = QueryRewriter()
    queries = rewriter.rewrite_queries(
        company_name=organ,
        context={"organ_no": organ_no}
    )
    
    # Step 2：並行多源搜尋
    from ..services.multi_source_search import MultiSourceSearch
    
    multi_search = MultiSourceSearch()
    search_results = multi_search.parallel_search(queries)
    
    if not search_results:
        raise ExternalServiceError(
            "No search results found from any source"
        )
    
    logger.info(f"搜尋到 {len(search_results)} 個結果")
    
    # 提取內容
    raw_content = search_results[0]['snippet'] if search_results else ""
    
    # Step 3：繼續原有流程...
```

#### 檢查清單：Phase 1.2
- [ ] 建立 `src/services/multi_source_search.py`
- [ ] 實現並行搜尋邏輯
- [ ] 實現結果聚合和排序
- [ ] 整合到 `generate_brief.py`
- [ ] 測試並行搜尋性能
- [ ] 監測 API 成本增加

---

## Phase 2：改進內容生成 (1.5-2 週)

### 2.1 強化 Prompt 設計

#### Step 1：建立高級 Prompt 構建模塊

**新文件：** `src/functions/utils/advanced_prompt_builder.py`

```python
"""
高級 Prompt 構建 - 生成結構化、有依據的簡介
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class AdvancedPromptBuilder:
    """構建高質量簡介的 Prompt"""
    
    # 禁用詞彙清單 - 避免通用詞彙
    BANNED_PHRASES = [
        "專業", "高質量", "優秀", "領先", "一流",
        "高效", "創新", "先進", "最好", "最強",
        "致力於", "擁有", "擁抱", "堅持",
        "以...為主", "提供服務", "為客戶服務"
    ]
    
    def build_generate_prompt(
        self,
        organ: str,
        organ_no: str,
        search_results: List[Dict],
        user_brief: str = None,
        style: str = "professional"
    ) -> str:
        """
        構建生成簡介的高級 Prompt
        
        Args:
            organ: 公司名稱
            organ_no: 統一編號
            search_results: 搜尋結果列表
            user_brief: 用戶提供的簡介
            style: 簡介風格
        
        Returns:
            完整的 Prompt 文本
        """
        
        # 格式化搜尋結果
        formatted_results = self._format_search_results(search_results)
        
        # 構建 Prompt
        prompt = f"""
你是一位企業簡介撰寫專家。根據以下信息編寫一份專業的公司簡介。

【公司信息】
公司名稱：{organ}
統一編號：{organ_no}

【搜尋結果】
{formatted_results}

【用戶提供的信息】
{user_brief or '無'}

【撰寫要求】

1. 結構要求（必須包含以下四個部分）：
   a) 開場（1-2句）：公司身份和主要業務
   b) 核心（3-5句）：具體業務詳情和獨特優勢，每句必須有[來源]標註
   c) 服務（2-3句）：主要產品和服務清單
   d) 認可（1-2句）：資質認證和重要成就

2. 內容質量要求：
   ✓ 避免以下詞彙：{', '.join(self.BANNED_PHRASES)}
   ✓ 包含具體數字、日期、名稱（而非"許多""眾多""大量"）
   ✓ 使用短句，平均 15-20 個字
   ✓ 邏輯清晰，按時間/重要性排序
   ✓ 每個重要陳述必須在[來源]中找到依據

3. 來源標註規則：
   - 格式：陳述內容 [來源: URL 或 Tavily]
   - 示例：公司於 2020 年成立 [來源: 官網]
   - 無來源的描述（推測、通用詞）禁止使用

4. 字數限制：
   - 總字數：200-300 字
   - 開場：20-30 字
   - 核心：80-120 字
   - 服務：40-60 字
   - 認可：30-50 字

【輸出格式】

必須返回有效的 JSON：
{{
    "title": "簡潔有力的標題（4-8字，包含公司名稱和行業）",
    "summary": "一句核心描述（20-30字，答覆'這家公司是做什麼的'）",
    "body_html": "<p>開場...</p><p>核心...</p><p>服務...</p><p>認可...</p>",
    "word_count": 250,
    "source_citations": {{
        "sentence_1": "https://...",
        "sentence_2": "Tavily",
        "...": "..."
    }},
    "quality_notes": "質量說明（如有特殊情況）",
    "confidence_score": 0.85
}}

【質量檢查清單】

在生成前先自問：
□ 有沒有使用禁用詞彙？
□ 是否包含具體數字或名稱？
□ 是否每個陳述都有來源？
□ 結構是否完整（開場→核心→服務→認可）？
□ 語言是否簡潔清晰？
□ 字數是否在 200-300 範圍內？

如果任何檢查項不符合，重新編寫直到符合。
"""
        
        return prompt.strip()
    
    def _format_search_results(self, search_results: List[Dict]) -> str:
        """格式化搜尋結果，供 Prompt 使用"""
        
        if not search_results:
            return "無搜尋結果"
        
        formatted = []
        for i, result in enumerate(search_results[:5], 1):
            url = result.get('url', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')[:200]  # 限制長度
            
            formatted.append(
                f"{i}. [{title}]\n"
                f"   URL: {url}\n"
                f"   摘要: {snippet}"
            )
        
        return "\n\n".join(formatted)
    
    def validate_generated_content(self, content: str, min_score: float = 0.75) -> Dict:
        """
        驗證生成的內容是否符合質量標準
        
        Returns:
            {
                'passed': bool,
                'score': float,
                'issues': [str],
                'suggestions': [str]
            }
        """
        issues = []
        suggestions = []
        score = 1.0
        
        # 檢查禁用詞彙
        for phrase in self.BANNED_PHRASES:
            if phrase in content:
                issues.append(f"包含禁用詞彙：{phrase}")
                score -= 0.05
                suggestions.append(f"用更具體的描述替換'{phrase}'")
        
        # 檢查結構
        if "<p>" not in content:
            issues.append("缺少段落標籤")
            score -= 0.1
        
        # 檢查來源標註
        if "[來源:" not in content:
            issues.append("缺少來源標註")
            score -= 0.15
            suggestions.append("為每個陳述添加 [來源] 標註")
        
        # 檢查字數
        word_count = len(content)
        if word_count < 200 or word_count > 350:
            issues.append(f"字數 {word_count}，應在 200-300")
            score -= 0.1
        
        return {
            'passed': score >= min_score,
            'score': max(0, score),
            'issues': issues,
            'suggestions': suggestions
        }


# 使用示例
if __name__ == "__main__":
    builder = AdvancedPromptBuilder()
    
    search_results = [
        {
            'url': 'https://example.com',
            'title': '台灣AI新創公司官網',
            'snippet': '專注自然語言處理技術的台灣新創公司...'
        }
    ]
    
    prompt = builder.build_generate_prompt(
        organ="台灣AI新創公司",
        organ_no="12345678",
        search_results=search_results,
        user_brief="一家專注 NLP 的新創公司"
    )
    
    print(prompt)
```

#### Step 2：整合到生成流程

**修改文件：** `src/functions/utils/generate_brief.py`

```python
def _generate_brief_traditional(data):
    # ... 前面的搜尋步驟 ...
    
    # Step 3：使用高級 Prompt 構建器
    from .advanced_prompt_builder import AdvancedPromptBuilder
    
    prompt_builder = AdvancedPromptBuilder()
    prompt = prompt_builder.build_generate_prompt(
        organ=organ,
        organ_no=organ_no,
        search_results=search_results,
        user_brief=data.get("brief")
    )
    
    logger.info("使用高級 Prompt 構建生成簡介")
    
    # Step 4：呼叫 LLM
    llm_result = call_llm(prompt)
    
    # Step 5：驗證生成內容
    validation = prompt_builder.validate_generated_content(
        llm_result.get("body_html", "")
    )
    
    if not validation['passed']:
        logger.warning(f"內容質量未達標：{validation['issues']}")
        # 可選：嘗試重新生成或返回警告
    
    result = post_process(llm_result)
    result['quality_validation'] = validation
    
    return result
```

#### 檢查清單：Phase 2.1
- [ ] 建立 `src/functions/utils/advanced_prompt_builder.py`
- [ ] 定義禁用詞彙清單和質量標準
- [ ] 實現 Prompt 構建邏輯
- [ ] 實現內容驗證函數
- [ ] 整合到生成流程
- [ ] 測試生成內容質量提升

---

## Phase 3-5：後續優化（按優先級跟進）

### 簡要計劃

| Phase | 功能 | 時間 | 難度 |
|-------|------|------|------|
| 3 | 查詢模板庫 + 關鍵字擴展 | 1 周 | 中 |
| 4 | LangGraph 節點優化 | 2 周 | 高 |
| 5 | 可觀測性和反饋 | 1 周 | 低 |

---

## 測試計劃

### 單元測試

```python
# tests/test_query_rewriter.py
import pytest
from src.services.query_rewriter import QueryRewriter

def test_query_rewriter_generates_multiple_queries():
    rewriter = QueryRewriter()
    queries = rewriter.rewrite_queries("台灣AI新創")
    
    assert len(queries) == 5
    assert "台灣AI新創" in " ".join(queries)
    assert len(set(queries)) == 5  # 確保沒有重複

def test_query_rewriter_handles_context():
    rewriter = QueryRewriter()
    queries = rewriter.rewrite_queries(
        "台灣AI新創",
        context={"organ_no": "12345678"}
    )
    
    # 至少有一個查詢包含統一編號
    assert any("12345678" in q for q in queries)
```

### 集成測試

```python
# tests/test_multi_source_search.py
from src.services.multi_source_search import MultiSourceSearch

def test_parallel_search_aggregates_results():
    search = MultiSourceSearch()
    queries = ["台灣AI新創 官網", "台灣AI新創 公司"]
    
    results = search.parallel_search(queries)
    
    assert len(results) > 0
    assert all('url' in r for r in results)
    assert all('sources' in r for r in results)
```

### 端到端測試

```bash
# 手動測試
curl -X POST http://localhost:5000/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{
    "organ": "台灣AI新創公司",
    "organNo": "12345678",
    "mode": "GENERATE"
  }' | jq .
```

檢查項：
- [ ] 搜尋使用多個查詢
- [ ] 結果包含來源標註
- [ ] 內容避免禁用詞彙
- [ ] 響應時間在 15 秒內

---

## 監測指標

### 關鍵績效指標（KPI）

建議在 `src/functions/utils/structured_logger.py` 中記錄：

```python
class PerformanceMetrics:
    def log_generation_metrics(self, organ, metrics):
        """記錄生成指標"""
        self.logger.info({
            'event': 'generation_complete',
            'organ': organ,
            'search_queries_used': metrics['queries_used'],
            'search_sources_used': metrics['sources'],
            'quality_score': metrics['quality_score'],
            'word_count': metrics['word_count'],
            'execution_time_seconds': metrics['execution_time'],
            'timestamp': datetime.now().isoformat()
        })
```

監測指標：
- 檢索精準度（搜尋結果相關性）
- 內容具體度（禁用詞彙比例、具體數字比例）
- 誤植率（事實檢核通過率）
- 執行時間（響應延遲）
- API 成本（調用數和成本）

---

## 常見問題 (FAQ)

### Q1：如何平衡搜尋成本和質量？

**A：** 建議採用分層策略：
1. 先用單一查詢嘗試（成本低）
2. 如果結果質量低（< 0.7 分），啟動多源並行搜尋
3. 使用結果緩存減少重複搜尋

### Q2：多源搜尋會增加多少延遲？

**A：** 理想情況下：
- 單源：8-10 秒
- 多源並行：10-12 秒（因為是並行，增加不多）
- 成本：增加約 2-3 倍 API 調用

### Q3：如何測試 Prompt 改進是否有效？

**A：** 建議：
1. 準備 10-20 個測試公司
2. 對比舊 Prompt vs 新 Prompt 的結果
3. 由人類評估內容質量（具體度、準確度）
4. 計算平均改進百分比

### Q4：如何處理搜尋結果為空的情況？

**A：** 建議降級策略：
1. 自動簡化查詢（去掉修飾詞）
2. 嘗試只用公司名稱搜尋
3. 使用備選來源（如 Google）
4. 最後 fallback：返回用戶提供的簡介或生成通用簡介

---

## 下一步行動

### 立即開始（本週）
1. [ ] 建立 `src/services/query_rewriter.py`
2. [ ] 建立 `src/functions/utils/advanced_prompt_builder.py`
3. [ ] 編寫基本測試

### 本月目標
1. [ ] Phase 1.1 完成（查詢重寫）
2. [ ] Phase 1.2 完成（並行搜尋）
3. [ ] Phase 2.1 完成（強化 Prompt）
4. [ ] 與 LangGraph 集成

### 後續月份
1. [ ] Phase 2.2（事實檢核）
2. [ ] Phase 3（查詢模板）
3. [ ] Phase 4-5（優化和監測）

---

## 資源需求

### 人力
- 1 名主要開發者（4-6 週）
- Code review：偶爾

### 技術棧
- Python 3.8+
- LangChain / LangGraph
- Claude 或 Gemini API
- Tavily + Serper API

### 成本估計
- 初期開發：0 元（使用現有 API）
- 上線後：API 成本增加 50-100%（因多源搜尋和驗證）

---

*最後更新：2024年4月*
*聯繫：[你的聯絡方式]*

