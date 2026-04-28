# Phase 17：架構設計

**日期**: 2026-04-17  
**版本**: v1.0.0

---

## 🎯 設計目標

根據用戶需求，實現真正的平行 LLM API 呼叫：
1. 同時發送多個獨立 Prompt（每個面向一個）
2. 使用 ThreadPoolExecutor 平行執行
3. 彙整所有 API 返回後再往下流程
4. 支援配置驅動

---

## 📊 當前架構 vs 目標架構

### 當前架構（問題）

```
┌─────────────────────────────────────────────────────────────┐
│  search_node                                               │
│  config_search(f"{state['organ']} 官網")                   │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  ConfigDrivenSearchTool                                    │
│  - 讀取配置                                                │
│  - 建立工具                                                │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  GeminiFewShotSearchTool                                   │
│  - 單一 Prompt（包含 4 面向）                              │
│  - 單次 API 呼叫                                           │
│  - 1,856 字元的複雜 Prompt                                │
└─────────────────────────────────────────────────────────────┘
```

**問題**：
- ❌ 單次查詢，速度慢（10-12s）
- ❌ Prompt 過長（1,856 字元）
- ❌ 無法根據場景選擇策略

---

### 目標架構（解決方案）

```
┌─────────────────────────────────────────────────────────────┐
│  主流程層 (company_brief_graph.py)                          │
│  search_node(state)                                        │
│  - 透過抽象工具類調用                                      │
│  - 接收平行工具返回的結果                                  │
└────────────────────┬──────────────────────────────────────┘
                     │ search(query, strategy="complete")
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  配置驅動層 (config_driven_search.py)                       │
│  - 讀取配置                                                │
│  - 根據 strategy 選擇配置                                  │
│  - 建立對應的工具                                          │
└────────────────────┬──────────────────────────────────────┘
                     │ tool.search(query)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  工具層 (search_tools.py)                                  │
│  ParallelAspectSearchTool                                  │
│  - 指定 API: Gemini API                                     │
│  - 指定 Prompt: 4 個面向的獨立 Prompt                       │
│  - 平行執行: ThreadPoolExecutor                            │
│  - 返回: 4 個面向的結果                                    │
└────────────────────┬──────────────────────────────────────┘
                     │ 4 個並發 API 呼叫
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM API 層 (Google Gemini)                                │
│  4 個並發的 API 呼叫                                       │
│  - gemini.search("foundation prompt")                       │
│  - gemini.search("core prompt")                            │
│  - gemini.search("vibe prompt")                           │
│  - gemini.search("future prompt")                         │
└─────────────────────────────────────────────────────────────┘
```

**優勢**：
- ✅ 平行執行，速度快（6-8s）
- ✅ Prompt 拆分（每個 ~200 字元）
- ✅ 可根據場景選擇策略

---

## 🏗️ 三層架構設計

### 層級職責

| 層級 | 檔案 | 職責 | 實例緩存 |
|------|------|------|----------|
| **主流程層** | `company_brief_graph.py` | 協調、結果處理 | 無 |
| **配置驅動層** | `config_driven_search.py` | 配置讀取、工廠模式 | 工具實例 |
| **工具層** | `search_tools.py` | 具體執行邏輯 | 工具類別 |

### 類別設計

```
BaseSearchTool (ABC)
    │
    ├── TavilyBatchSearchTool
    ├── GeminiFewShotSearchTool
    ├── GeminiPlannerTavilyTool
    ├── ParallelMultiSourceTool
    └── ParallelAspectSearchTool (新增)
            │
            ├── ASPECT_PROMPTS (4 個面向的 Prompt)
            ├── search() (平行執行)
            └── _search_single_aspect() (單個查詢)
```

---

## 📝 Prompt 設計

### 當前 Prompt（Phase 16）

```python
# 單一 Prompt，包含所有面向（1,856 字元）
GEMINI_PROMPT_TEMPLATE = """你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊...

【核心任務】
根據搜尋結果，提取公司的四個面向的資訊...

【輸出格式】
{
    "foundation": "...",
    "core": "...",
    "vibe": "...",
    "future": "..."
}

【特別要求】
1. 信息準確性...
2. 字數控制...
3. 去重和合併...
...

【輸出檢查清單】
...
"""
```

### 目標 Prompt（Phase 17）

```python
# 4 個獨立的 Prompt（每個 ~200 字元）

ASPECT_PROMPTS = {
    "foundation": """搜尋「{company}」的品牌實力與基本資料。
包括：成立時間、統一編號、資本額、公司地址、規模、主要投資方等。
返回 JSON 格式。""",

    "core": """搜尋「{company}」的技術產品與服務核心。
包括：主要產品、技術亮點、服務內容、核心競爭力等。
返回 JSON 格式。""",

    "vibe": """搜尋「{company}」的職場環境與企業文化。
包括：員工評價、工作氛圍、企業文化、團隊特色等。
返回 JSON 格式。""",

    "future": """搜尋「{company}」的近期動態與未來展望。
包括：最新新聞、發展計劃、投資動向、市場前景等。
返回 JSON 格式。"""
}
```

### 對比

| 項目 | 當前 | 目標 |
|------|------|------|
| Prompt 數量 | 1 個 | 4 個 |
| 總長度 | 1,856 字元 | ~800 字元 |
| 每個 Prompt | N/A | ~200 字元 |
| 執行方式 | 串列 | 平行 |

---

## ⚙️ 配置設計

### 當前配置

```json
{
  "search": {
    "provider": "gemini_fewshot",
    "max_results": 3
  }
}
```

### 目標配置

```json
{
  "strategies": {
    "fast": {
      "provider": "tavily",
      "description": "快速驗證"
    },
    "basic": {
      "provider": "gemini_fewshot",
      "description": "基本簡介"
    },
    "complete": {
      "provider": "parallel_aspect_search",
      "parallel": true,
      "max_workers": 4,
      "aspects": ["foundation", "core", "vibe", "future"],
      "timeout": 15
    },
    "deep": {
      "provider": "parallel_multi_source",
      "parallel": true,
      "sources": ["gemini", "tavily"]
    }
  },
  "default_strategy": "complete",
  "models": {
    "gemini": {
      "model": "gemini-2.0-flash",
      "temperature": 0.2
    }
  }
}
```

---

## 🔄 流程對比

### 當前流程

```
search_node(state)
    │
    ├─→ config_search("台積電 官網")
    │        │
    │        └─→ GeminiFewShotSearchTool.search()
    │                 │
    │                 ├─→ 1 個 Prompt（1,856 字元）
    │                 ├─→ 1 次 API 呼叫
    │                 └─→ 返回結果
    │
    └─→ 處理結果
         └─→ 傳給 Summary Node
```

### 目標流程

```
search_node(state)
    │
    ├─→ config_search("台積電", strategy="complete")
    │        │
    │        └─→ ParallelAspectSearchTool.search()
    │                 │
    │                 ├─→ 建立 4 個 Prompt
    │                 ├─→ ThreadPoolExecutor(4)
    │                 │    │
    │                 │    ├─→ Thread-1: foundation API
    │                 │    ├─→ Thread-2: core API
    │                 │    ├─→ Thread-3: vibe API
    │                 │    └─→ Thread-4: future API
    │                 │
    │                 └─→ 彙整結果
    │
    └─→ 處理結果
         └─→ 傳給 Summary Node
```

---

## 📊 效能預期

### 理論計算

```
單個面向查詢時間：~3-5s

平行查詢 4 個面向：
  - 理論最佳：~3-5s（最慢的那個決定）
  - 實際預期：~6-8s（包含協調開銷）

當前（gemini_fewshot）：~10-12s
改善幅度：~40-50%
```

### 風險評估

| 風險 | 影響 | 機率 | 緩解 |
|------|------|------|------|
| API 速率限制 | 高 | 中 | 加入重試機制 |
| 記憶體增加 | 中 | 低 | 限制 max_workers |
| 錯誤處理 | 中 | 高 | 完善的異常處理 |
| 結果不一致 | 低 | 中 | 結果驗證 |

---

## ✅ 設計總結

### 關鍵設計點

1. **Prompt 拆分**：4 個獨立 Prompt，每個面向一個
2. **平行執行**：ThreadPoolExecutor，4 個並發
3. **配置驅動**：可透過 config 切換策略
4. **工具緩存**：單例模式，避免重複創建
5. **錯誤隔離**：單個失敗不影響其他

### 預期效益

- **效能提升**：40-50%（10-12s → 6-8s）
- **架構清晰**：三層分離，職責明確
- **成本可控**：可選擇不同策略
- **可維護性**：每個類別 < 200 行

---

*設計完成時間：2026-04-17*