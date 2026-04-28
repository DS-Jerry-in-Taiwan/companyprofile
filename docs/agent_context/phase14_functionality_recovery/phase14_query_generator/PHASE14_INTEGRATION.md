# Phase 14: 四面向流程整合

## 目標

將測試模組驗證可行的「四面向流程」整合到主流程 LangGraph：
- 新增 `summary_node` 進行四面向彙整
- 修改 `generate_node` 接收四面向輸入
- 將 `summarizer.py` 移入 `src/langgraph_state/`

---

## 現況分析

### 測試模組流程

```
parallel_runner.py
    │
    ├── generate_queries()      # 四面向查詢生成
    ├── Tavily/Gemini 搜尋       # 平行搜尋
    ├── summarizer.py           # 四面向彙整
    └── brief_generator.py      # 簡介生成
```

### 主流程 LangGraph 現況

```
company_brief_graph.py
    │
    ├── search_node            # 搜尋（已有）
    ├── generate_node         # 生成（需修改）
    └── quality_check_node     # 品質檢查（已有）
```

### 整合後 LangGraph

```
company_brief_graph.py
    │
    ├── search_node            # 搜尋（已有）
    ├── summary_node          # 【新增】四面向彙整
    ├── generate_node         # 【修改】接收四面向
    └── quality_check_node     # 品質檢查（已有）
```

---

## 工項總覽

| # | 工項 | 檔案 | 狀態 |
|---|------|------|------|
| 1 | 搬移 summarizer.py | `src/langgraph_state/summarizer.py` | ✅ 完成 |
| 2 | 更新 state.py | 新增四面向欄位和類別 | ✅ 完成 |
| 3 | 新增 summary_node | 四面向彙整節點 | ✅ 完成 |
| 4 | 修改 generate_node | 接收四面向輸入 | ✅ 完成 |
| 5 | 更新節點圖 | 加入 summary_node | ✅ 完成 |
| 6 | 測試驗證 | 確認流程正常 | ✅ 完成 |

---

## 逐步開發規劃

---

### Step 1: 搬移 summarizer.py

**目的：** 將測試模組的 `summarizer.py` 移入 `src/langgraph_state/`

**動作：**
1. 建立 `src/langgraph_state/summarizer.py`
2. 複製測試模組 `summarizer.py` 的內容
3. 調整路徑（移除 PROJECT_ROOT 計算）

**預期產出：**

```
src/langgraph_state/
├── summarizer.py              # 【新增】四面向彙整器
├── state.py                   # 【待更新】
├── company_brief_graph.py      # 【待更新】
└── __init__.py               # 【待更新】
```

**驗證標準：**
```bash
python -c "from src.langgraph_state.summarizer import FourAspectSummarizer, AspectSummary; print('OK')"
```

---

### Step 2: 更新 state.py

**目的：** 在狀態中新增四面向相關欄位

**動作：**
1. 新增 `AspectSummaryResult` dataclass
2. 在 `CompanyBriefState` 新增 `aspect_summaries` 欄位
3. 在 `NodeNames` 新增 `SUMMARY = "summary"`

**預期產出：**

**state.py 新增內容：**
```python
# 新增 dataclass
@dataclass
class AspectSummaryResult:
    """四面向彙整結果"""
    aspect: str
    description: str
    content: str
    source_queries: int
    total_characters: int

# CompanyBriefState 新增欄位
class CompanyBriefState(TypedDict):
    # ... 現有欄位 ...

    # 新增
    aspect_summaries: Optional[Dict[str, AspectSummaryResult]]

# NodeNames 新增
class NodeNames:
    # ... 現有 ...
    SUMMARY = "summary"
```

**驗證標準：**
```python
from src.langgraph_state.state import CompanyBriefState, AspectSummaryResult, NodeNames
assert NodeNames.SUMMARY == "summary"
# state 可以包含 aspect_summaries
```

---

### Step 3: 新增 summary_node

**目的：** 建立四面向彙整節點

**動作：**
1. 在 `company_brief_graph.py` 新增 `summary_node` 函式
2. 接收 `search_result`（多個查詢結果）
3. 輸出 `aspect_summaries`（四面向彙整結果）

**預期產出：**

```python
# company_brief_graph.py 新增

def summary_node(state: CompanyBriefState) -> CompanyBriefState:
    """
    彙整節點 - 將搜尋結果彙整為四個面向

    輸入：
        state["search_result"] - 搜尋結果

    輸出：
        state["aspect_summaries"] - 四面向彙整結果
    """
    from src.langgraph_state.summarizer import FourAspectSummarizer

    # 從 state 取得搜尋結果（需要調整 search_result 格式）
    # ...

    # 彙整
    summarizer = FourAspectSummarizer()
    summaries = summarizer.summarize(query_results)

    # 更新 state
    state["aspect_summaries"] = summaries
    return state
```

**驗證標準：**
```python
# 可以正確建立節點
from src.langgraph_state.company_brief_graph import summary_node
assert callable(summary_node)
```

---

### Step 4: 修改 generate_node

**目的：** 讓 generate_node 接收四面向輸入

**動作：**
1. 修改 `generate_node` 函式
2. 接收 `state["aspect_summaries"]`
3. 調整 prompt 建構邏輯

**預期產出：**

```python
# company_brief_graph.py 修改 generate_node

def generate_node(state: CompanyBriefState) -> CompanyBriefState:
    # ...

    # 新增：使用四面向內容
    aspect_summaries = state.get("aspect_summaries")

    if aspect_summaries:
        # 四面向模式
        foundation = aspect_summaries.get("foundation", {}).get("content", "")
        core = aspect_summaries.get("core", {}).get("content", "")
        vibe = aspect_summaries.get("vibe", {}).get("content", "")
        future = aspect_summaries.get("future", {}).get("content", "")

        # 呼叫 LLM 生成簡介
        # ...
    else:
        # 現有模式（向後相容）
        # ...
```

**驗證標準：**
```python
# generate_node 可以處理有/無 aspect_summaries 的情況
```

---

### Step 5: 更新節點圖

**目的：** 在 LangGraph 中加入 summary_node

**動作：**
1. 在 `create_company_brief_graph()` 中新增 summary_node
2. 設定節點順序：`search → summary → generate → quality_check`

**預期產出：**

```python
# company_brief_graph.py

def create_company_brief_graph():
    # ...
    graph = StateGraph(CompanyBriefState)

    # 新增節點
    graph.add_node(NodeNames.SEARCH, search_node)
    graph.add_node(NodeNames.SUMMARY, summary_node)      # 【新增】
    graph.add_node(NodeNames.GENERATE, generate_node)
    graph.add_node(NodeNames.QUALITY_CHECK, quality_check_node)

    # 設定順序
    graph.add_edge(NodeNames.START, NodeNames.SEARCH)
    graph.add_edge(NodeNames.SEARCH, NodeNames.SUMMARY)  # 【新增】
    graph.add_edge(NodeNames.SUMMARY, NodeNames.GENERATE) # 【新增】
    graph.add_edge(NodeNames.GENERATE, NodeNames.QUALITY_CHECK)
    # ...
```

**驗證標準：**
```python
graph = create_company_brief_graph()
assert "summary" in graph.nodes
```

---

### Step 6: 整合測試

**目的：** 確認完整流程正常運作

**動作：**
1. 執行 API 或 LangGraph 測試
2. 確認四面向彙整正確
3. 確認簡介生成正確

**驗證情境：**

```bash
# 情境 1: 使用四面向流程
# 預期：aspect_summaries 有值，generate_node 使用四面向內容

# 情境 2: 不使用四面向流程（向後相容）
# 預期：aspect_summaries 為空，generate_node 使用現有邏輯
```

**驗證標準：**
- 四面向流程產出正確格式的簡介
- 向後相容：不傳 aspect_summaries 也能正常運作

---

## 檔案變更總覽

| 檔案 | 變更 |
|------|------|
| `src/langgraph_state/summarizer.py` | 新增（從測試模組搬移） |
| `src/langgraph_state/state.py` | 新增 dataclass、欄位 |
| `src/langgraph_state/company_brief_graph.py` | 新增 summary_node、修改 generate_node、更新圖 |
| `src/langgraph_state/__init__.py` | 更新匯出 |

---

## 產出檢核清單

| Step | 項目 | 驗證 | 狀態 |
|------|------|------|------|
| 1 | summarizer.py 搬移 | `from src.langgraph_state.summarizer import *` | ✅ |
| 2 | state.py 更新 | `AspectSummaryResult` 可使用 | ✅ |
| 3 | summary_node 新增 | `summary_node` 可呼叫 | ✅ |
| 4 | generate_node 修改 | 可接收 aspect_summaries | ✅ |
| 5 | 節點圖更新 | graph 包含 summary | ✅ |
| 6 | 整合測試 | 流程正常產出簡介 | ✅ |

---

## 估計工時

| Step | 工項 | 估計時間 |
|------|------|----------|
| 1 | 搬移 summarizer.py | 10 分鐘 |
| 2 | 更新 state.py | 15 分鐘 |
| 3 | 新增 summary_node | 20 分鐘 |
| 4 | 修改 generate_node | 20 分鐘 |
| 5 | 更新節點圖 | 15 分鐘 |
| 6 | 整合測試 | 30 分鐘 |
| **總計** | | **~110 分鐘** |

---

## 向後相容

- `generate_node` 需同時支援：
  - 有 `aspect_summaries`：使用四面向內容
  - 無 `aspect_summaries`：使用現有邏輯（向後相容）

---

## 待確認事項

| 項目 | 問題 |
|------|------|
| search_result 格式 | 目前是 `SearchResult` dataclass，是否需要調整？ |
| 四面向查詢數量 | 固定 8 個查詢？還是需要動態？ |
| Layer 5, 6 | 標籤生成、內容評估是否納入？ |
