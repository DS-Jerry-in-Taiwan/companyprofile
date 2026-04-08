# OrganBriefOptimization 項目優化戰略

## 當前狀況分析

### 存在的問題
1. **查詢結果不精準**：當前使用簡單的關鍵字搜尋，缺乏語意理解和多輪查詢優化
2. **內容空泛**：生成的簡介缺乏具體細節，prompt 不夠嚴格
3. **內容誤植**：生成內容與檢索內容關聯度不足，缺乏事實檢核
4. **查詢關鍵字與模板不足**：查詢策略單一，無自適應查詢優化

### 當前架構特點
- 已建立 LangGraph 框架基礎（state.py 和 company_brief_graph.py）
- 支持傳統流程和 LangGraph 流程的雙軌制
- 具有基本的重試和 fallback 機制
- 使用 Tavily 作為主要搜尋源，Serper 作為備選

---

## 優化路線圖

### Phase 1：改進檢索層（高優先級）

#### 1.1 多維度查詢策略
```
目標：提升檢索精準度和覆蓋率

實施步驟：
1. 實現查詢重寫引擎
   - 基於用戶輸入自動生成 3-5 個變異查詢
   - 包含：公司名稱、統一編號、行業關鍵詞、相關產品
   - 示例：
     * "{{company_name}} 官網"
     * "{{company_name}} 統一編號 {{organ_no}}"
     * "{{company_name}} {{industry}} 服務"
     * "{{company_name}} 公司資訊"

2. 並行執行多個查詢
   - 使用 LangGraph 並行節點並行執行不同查詢
   - 每個查詢使用不同的搜尋源（Tavily + Serper + Google）
   - 聚合和去重搜尋結果

3. 實現查詢結果排序
   - 使用 cross-encoder 對搜尋結果進行語意相關度排序
   - 基於結果中出現的關鍵詞密度加權排序
```

#### 1.2 向量檢索增強
```
目標：從知識庫中精準提取相關信息

實施步驟：
1. 建立向量資料庫
   - 集成 Qdrant 或 Chroma 作為向量存儲
   - 對公司資料建立 embedding 索引

2. 實現混合檢索
   - BM25 (關鍵詞檢索) + Embedding (語意檢索)
   - 使用 LLM 生成多個查詢視角的 embedding
   - 聚合檢索結果

配置文件示例：
```python
# src/services/vector_search.py
class VectorSearchService:
    def __init__(self):
        self.client = QdrantClient("http://localhost:6333")
        self.embedder = HuggingFaceEmbeddings()
    
    def hybrid_search(self, query, company_id, top_k=5):
        # BM25 檢索
        bm25_results = self._bm25_search(query, company_id)
        # 向量檢索
        vector_results = self._vector_search(query, company_id)
        # 結果融合和排序
        return self._fusion_and_rank(bm25_results, vector_results)
```

---

### Phase 2：改進內容生成（高優先級）

#### 2.1 強化 Prompt 設計
```
目標：生成具體、有依據的簡介

新 Prompt 框架：
1. 明確結構要求
   - 開場：公司身份和主要業務（1-2句）
   - 核心：具體業務詳情和優勢（3-5句，必須引用來源）
   - 服務：主要產品和服務清單（2-3句）
   - 認可：資質認證和成就（1-2句）

2. 來源標註要求
   - 每個陳述必須附帶 [來源: URL] 或 [來源: Tavily]
   - 禁止無依據的描述

3. 質量控制要求
   - 避免通用詞彙（如：專業、高質量、優秀）
   - 必須包含具體數字、名稱、日期
   - 字數限制控制（e.g. 200-300 字）

新 Prompt 模板：
```python
# src/functions/utils/prompt_builder.py 新增方法
def build_generate_prompt_v2(organ, organ_no, search_results, user_brief, style):
    """
    生成高質量簡介的 Prompt 模板
    
    搜尋結果：
    {format_search_results(search_results)}
    
    公司信息：
    - 公司名稱：{organ}
    - 統一編號：{organ_no}
    - 用戶提供信息：{user_brief}
    
    要求：
    1. 根據上述搜尋結果編寫簡介，每個陳述必須有明確依據
    2. 結構：[開場] → [核心業務] → [產品服務] → [認可資質]
    3. 避免通用詞彙，使用具體數字和名稱
    4. 為每個陳述標註來源 [來源: ...]
    5. 總字數 200-300 字
    
    輸出格式（JSON）：
    {{
        "title": "簡潔有力的標題（4-8字）",
        "summary": "一句核心描述（20-30字）",
        "body_html": "<p>正文...</p><p>...</p>",
        "source_citations": {{"句子索引": "來源"}},
        "confidence_score": 0.0-1.0
    }}
    """
```

#### 2.2 多階段生成和驗證
```
目標：確保內容質量和準確性

流程：
1. 初始生成：LLM 根據檢索結果生成簡介
2. 事實檢查：驗證每個陳述是否在搜尋結果中有依據
3. 內容完善：如有缺陷，自動補充或重新生成
4. 品質評分：使用 LLM 自評內容品質

LangGraph 節點示例：
```python
# 在 src/langgraph/company_brief_graph.py 中新增

def fact_check_node(state: CompanyBriefState) -> CompanyBriefState:
    """事實檢核節點"""
    llm_result = state['llm_result']
    search_result = state['search_result']
    
    # 使用 LLM 驗證事實
    validation = llm.invoke(f"""
    驗證以下簡介是否與搜尋結果一致：
    簡介：{llm_result.body_html}
    搜尋結果：{search_result.answer}
    
    返回：
    1. 事實準確性評分 (0-1)
    2. 有問題的陳述清單
    3. 修正建議
    """)
    
    # 根據驗證結果決定是否需要重新生成
    if validation['accuracy_score'] < 0.8:
        state['llm_result'].confidence_score = validation['accuracy_score']
    
    return state
```

---

### Phase 3：實現查詢模板和關鍵字擴展（中優先級）

#### 3.1 查詢模板庫
```
目標：支援不同查詢意圖，自動選擇最合適的模板

實施步驟：
1. 定義查詢模板
```python
# src/services/query_templates.py

QUERY_TEMPLATES = {
    "basic_info": {
        "patterns": ["什麼是", "介紹"],
        "templates": [
            "{company_name} 官網",
            "{company_name} 公司介紹",
            "{company_name} 是做什麼的"
        ]
    },
    "products": {
        "patterns": ["產品", "服務", "主要業務"],
        "templates": [
            "{company_name} 產品",
            "{company_name} 服務內容",
            "{company_name} 主要業務範圍"
        ]
    },
    "credentials": {
        "patterns": ["認證", "資質", "獲獎"],
        "templates": [
            "{company_name} 認證資質",
            "{company_name} 榮譽獲獎",
            "{company_name} ISO 認證"
        ]
    },
    "scale": {
        "patterns": ["規模", "規模", "員工"],
        "templates": [
            "{company_name} 公司規模",
            "{company_name} 員工人數",
            "{company_name} 營收"
        ]
    }
}

def detect_query_intent(user_input: str) -> str:
    """根據用戶輸入檢測查詢意圖"""
    for intent, config in QUERY_TEMPLATES.items():
        if any(p in user_input for p in config['patterns']):
            return intent
    return "basic_info"  # 默認

def get_queries_for_intent(intent: str, company_name: str) -> List[str]:
    """獲取指定意圖的查詢模板"""
    templates = QUERY_TEMPLATES.get(intent, {}).get('templates', [])
    return [t.format(company_name=company_name) for t in templates]
```

#### 3.2 自動關鍵字擴展
```python
# src/services/query_expansion.py

class QueryExpansionService:
    def __init__(self):
        self.llm = ... # 初始化 LLM
    
    def expand_query(self, query: str, context: Dict) -> List[str]:
        """
        使用 LLM 自動擴展查詢關鍵字
        
        示例：
        輸入：台灣的 AI 新創公司
        輸出：
        - 台灣 AI 新創
        - 人工智能 新創公司 台灣
        - 台灣最新 AI 技術公司
        - 台灣深度學習公司
        """
        expansion_prompt = f"""
        給定查詢詞，生成 3-5 個相關的搜尋變異
        原始查詢：{query}
        背景信息：{context}
        
        要求：
        1. 包含同義詞替換
        2. 改變詞序
        3. 添加相關領域詞彙
        4. 保持查詢意圖不變
        """
        
        expanded = self.llm.invoke(expansion_prompt)
        return self._parse_expanded_queries(expanded)
```

---

### Phase 4：增強 LangGraph 流程（中優先級）

#### 4.1 並行檢索節點
```python
# 在 src/langgraph/company_brief_graph.py 中新增

def multi_source_search_node(state: CompanyBriefState) -> CompanyBriefState:
    """並行使用多個搜尋源"""
    queries = generate_queries(state['organ'])
    
    # 並行執行搜尋
    results = parallel_search(queries, sources=['tavily', 'serper', 'google'])
    
    # 聚合結果
    aggregated = aggregate_results(results)
    
    # 使用 cross-encoder 排序
    ranked = rerank_results(aggregated)
    
    state['search_results'] = ranked
    return state

def parallel_search(queries: List[str], sources: List[str]) -> List[SearchResult]:
    """使用多個來源並行搜尋"""
    import concurrent.futures
    
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        for query in queries:
            for source in sources:
                future = executor.submit(search_with_source, query, source)
                futures.append(future)
    
    return [f.result() for f in concurrent.futures.as_completed(futures)]
```

#### 4.2 品質檢查分支
```python
# 在 state.py 中新增節點

class NodeNames:
    # ... 現有內容 ...
    FACT_CHECK = "fact_check"
    QUALITY_SCORE = "quality_score"
    CONFIDENCE_FILTER = "confidence_filter"

def quality_check_node(state: CompanyBriefState) -> CompanyBriefState:
    """品質檢查節點"""
    # 檢查生成的內容是否滿足質量標準
    quality_metrics = evaluate_quality(state['llm_result'], state['search_result'])
    
    state['quality_check_result'] = QualityCheckResult(
        passed=quality_metrics['score'] >= 0.75,
        score=quality_metrics['score'],
        issues=quality_metrics['issues']
    )
    
    return state
```

---

### Phase 5：可觀測性和反饋閉環（低優先級）

#### 5.1 詳細日誌和指標
```python
# src/functions/utils/structured_logger.py 增強

class QueryPerformanceLogger:
    def log_query_attempt(self, query, source, results_count):
        """記錄查詢嘗試"""
        self.logger.info({
            'event': 'query_attempt',
            'query': query,
            'source': source,
            'results_count': results_count,
            'timestamp': datetime.now()
        })
    
    def log_generation_quality(self, organ, quality_score, issues):
        """記錄生成質量"""
        self.logger.info({
            'event': 'generation_quality',
            'organ': organ,
            'quality_score': quality_score,
            'issues': issues
        })
```

#### 5.2 用戶反饋機制
```python
# src/functions/utils/feedback_handler.py

class FeedbackHandler:
    def collect_feedback(self, organ_no: str, quality_rating: int, issues: List[str]):
        """收集用戶反饋"""
        # 存儲到數據庫
        # 用於後續優化
        pass
    
    def analyze_feedback(self) -> Dict:
        """分析反饋數據"""
        # 識別常見問題
        # 推薦優化方向
        pass
```

---

## 實施優先級

### 立即開始（This Sprint）
1. **Phase 2.1**：強化 Prompt 設計 - 最快見效
2. **Phase 1.1**：實現查詢重寫引擎

### 下一個迭代（Next Sprint）
1. **Phase 2.2**：多階段生成和驗證
2. **Phase 4.1**：並行檢索節點

### 後續迭代
1. **Phase 3**：查詢模板庫
2. **Phase 4.2**：品質檢查分支
3. **Phase 5**：可觀測性增強

---

## 預期效果

| 問題 | Phase | 優化措施 | 預期改善 |
|------|--------|----------|----------|
| 查詢不精準 | 1.1 + 1.2 | 多維度查詢 + 向量檢索 | 檢索精準度 +30-40% |
| 內容空泛 | 2.1 + 2.2 | 強化 Prompt + 事實檢查 | 內容具體度評分 +50% |
| 內容誤植 | 2.2 + 4.2 | 事實檢核 + 品質評分 | 誤植率 -80% |
| 查詢策略單一 | 3.1 + 3.2 | 模板庫 + 關鍵字擴展 | 覆蓋率 +25-35% |

---

## 技術債務清單

- [ ] 將錯誤處理從 try/except 整合到 LangGraph 錯誤節點
- [ ] 統一日誌系統
- [ ] 建立單元測試覆蓋率
- [ ] 優化 Tavily 和 Serper 的 API 成本

---

## 附錄：文件結構建議

```
src/
├── langgraph/
│   ├── company_brief_graph.py      # 當前：保留
│   ├── query_rewriter.py           # 新增：查詢重寫邏輯
│   └── state.py                    # 當前：擴展新節點類型
│
├── services/
│   ├── query_expansion.py          # 新增：關鍵字擴展
│   ├── query_templates.py          # 新增：查詢模板庫
│   ├── vector_search.py            # 新增：向量檢索
│   ├── fact_checker.py             # 新增：事實檢核
│   └── quality_evaluator.py        # 新增：品質評估
│
├── functions/
│   └── utils/
│       ├── prompt_builder.py       # 改進：新增 v2 Prompt 模板
│       ├── generate_brief.py       # 改進：支援多階段生成
│       └── feedback_handler.py     # 新增：反饋收集
```

