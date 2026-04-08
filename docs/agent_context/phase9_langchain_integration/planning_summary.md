# Phase 9：LangChain 整合與錯誤處理機制

## 一、階段目標

### 1.1 概述
本階段旨在將現有的系統模組整合至 LangChain 框架，建立統一的錯誤處理機制，並透過 LangGraph 實現動態路由能力。Phase 8 已完成 Tavily API 整合，本階段將在此基礎上進一步提升系統的穩定性、可擴展性與可維護性。

### 1.2 具體目標

| 目標類別 | 具體項目 | 成功指標 | 狀態 |
|----------|----------|----------|------|
| 錯誤處理 | 整合 RunnableRetry 與 RunnableWithFallbacks | 所有 API 呼叫具備重試與降級機制 | ✅ 已完成 |
| 動態路由 | 實作 LangGraph 狀態圖與條件邊 | 根據錯誤類型自動選擇處理路徑 | ✅ 已完成 |
| 工具封裝 | 將現有模組包裝為 LangChain Tool | Tavily/搜尋/LLM 等工具可複用 | ✅ 已完成 |
| 品質檢查 | 建立輸出品質驗證機制 | 生成結果通過率達 95% 以上 | ✅ 已完成 |
| 可選優化 | ~~快取機制與 A/B 測試框架~~ | ~~API 呼叫次數減少 30%~~ | ⏸️ 本階段不做 |

---

## 二、主要任務

### 任務總覽

| 任務編號 | 任務名稱 | 預估工時 | 依賴關係 | 狀態 |
|----------|----------|----------|----------|------|
| T9.0 | 修正 GENERATE 模式素材傳遞 | 4 小時 | Phase 8 完成 | ✅ 已完成 |
| T9.1 | LangChain 錯誤處理機制整合 | 8 小時 | T9.0 完成 | ✅ 已完成 |
| T9.2 | LangGraph 狀態圖實作 | 16 小時 | T9.1 完成 | ✅ 已完成 |
| T9.3 | LangChain Tool 包裝 | 12 小時 | T9.1 完成 | ✅ 已完成 |
| T9.4 | 品質檢查機制建立 | 8 小時 | T9.3 完成 | ✅ 已完成 |
| T9.5 | 快取機制實作（可選） | 8 小時 | T9.2 完成 | ⏸️ 本階段不做 |
| T9.6 | A/B 測試框架建置（可選） | 12 小時 | T9.4 完成 | ⏸️ 本階段不做 |

---

## 三、工項拆解

### 3.0 任務 T9.0：修正 GENERATE 模式素材傳遞（Phase 8 遺留問題）

#### 3.0.1 問題說明

Phase 8 完成的 GENERATE 模式只用了網路搜尋結果生成簡介，沒有把用戶提供的素材（organNo、brief）一起送給 LLM，導致生成的內容不夠準確。

#### 3.0.2 子任務拆解

| 子任務 | 說明 | 前置條件 | 輸入 | 輸出 |
|--------|------|----------|------|------|
| T9.0.1 | 修改 generate_brief.py 傳遞素材 | Phase 8 完成 | data 字典 | 更新後的 generate_brief.py |
| T9.0.2 | 修改 prompt_builder.py 組合素材 | T9.0.1 完成 | 所有素材參數 | 更新後的 prompt_builder.py |
| T9.0.3 | 測試驗證素材正確傳遞 | T9.0.2 完成 | 測試案例 | 測試通過 |

#### 3.0.3 詳細說明

本任務是修正 Phase 8 遺留的關鍵問題，確保所有用戶素材能正確傳遞至 LLM：

1. **修改 generate_brief.py**：
   - 取出 `data.get("organNo")` 和 `data.get("brief")`
   - 將這些素材一起傳給 prompt_builder

2. **修改 prompt_builder.py**：
   - 修改 `build_generate_prompt` 函式
   - 接收並組裝所有素材：organ, organNo, companyUrl, user_brief, web_content
   - 將所有素材一起送給 LLM

3. **修正後的流程**：
   ```
   用戶輸入（organ + organNo + companyUrl + brief）
            ↓
   網路搜尋取得更多資訊
            ↓
   合併所有素材 + 網路內容 → 送給 LLM
            ↓
   生成公司簡介
   ```

#### 3.0.4 為什麼這個任務重要

- 這是 Phase 8 遺留的關鍵問題
- 沒有正確傳遞用戶素材會導致生成的公司簡介不準確
- 影響後續 LangChain/LangGraph 整合的基礎正確性

---

### 3.1 任務 T9.1：LangChain 錯誤處理機制整合

#### 3.1.1 子任務拆解

| 子任務 | 說明 | 前置條件 | 輸入 | 輸出 |
|--------|------|----------|------|------|
| T9.1.1 | 建立統一的重試配置模組 | Phase 8 Tavily 整合完成 | 現有錯誤處理代碼 | `src/langchain/retry_config.py` |
| T9.1.2 | 實作 RunnableRetry 包裝器 | T9.1.1 完成 | API 呼叫函式 | 包裝後的可重試函式 |
| T9.1.3 | 實作 RunnableWithFallbacks | T9.1.2 完成 | 主要/備用函式 | 多級 Fallback 鏈 |
| T9.1.4 | 整合錯誤處理至現有服務 | T9.1.3 完成 | 各服務模組 | 更新後的服務模組 |

#### 3.1.2 詳細說明

本任務的核心是將 LangChain 的錯誤處理機制（`RunnableRetry` 與 `RunnableWithFallbacks`）整合至現有系統。具體來說：

1. **建立重試配置模組**：定義統一的重試策略，包括最大重試次數、初始回退時間、最大回退時間、 指數退避因子等參數。

2. **RunnableRetry 包裝器**：為現有的 API 呼叫函数包裝重試邏輯，自動處理暫時性錯誤（如網路超時、 503 服務不可用等）。

3. **RunnableWithFallbacks**：建立多級 Fallback 鏈，當主要服務失敗時，自動切換至備用服務。 例如：Tavily API → Serper API → 傳統爬蟲 → mock 資料。

4. **整合至現有服務**：將錯誤處理機制應用於 `generate_brief.py`、`tavily_client.py`、 `llm_service.py` 等關鍵模組。

---

### 3.2 任務 T9.2：LangGraph 狀態圖實作

#### 3.2.1 子任務拆解

| 子任務 | 說明 | 前置條件 | 輸入 | 輸出 |
|--------|------|----------|------|------|
| T9.2.1 | 定義狀態圖結構與節點 | T9.1 完成 | 業務流程需求 | `src/langgraph/state.py` |
| T9.2.2 | 實作條件邊路由邏輯 | T9.2.1 完成 | 狀態節點定義 | 條件判斷函式 |
| T9.2.3 | 建立錯誤處理分支 | T9.2.2 完成 | 錯誤類型定義 | 錯誤分支邏輯 |
| T9.2.4 | 整合狀態圖至主流程 | T9.2.3 完成 | 現有 generate_brief | 更新後的主流程 |

#### 3.2.2 詳細說明

本任務旨在建立 LangGraph 狀態圖，實現動態路由能力：

1. **狀態圖結構**：定義節點（Node）與邊（Edge），包括：
   - 起始節點（START）
   - 搜尋節點（Tavily Search）
   - LLM 生成節點（LLM Generation）
   - 品質檢查節點（Quality Check）
   - 結束節點（END）

2. **條件邊路由**：根據前一步的輸出結果，動態決定下一步：
   - 搜尋成功 → 進入 LLM 生成
   - 搜尋失敗 → 進入 Fallback 搜尋
   - 品質檢查失敗 → 進入重試或使用預設回應

3. **錯誤處理分支**：針對不同錯誤類型建立對應分支：
   - 網路錯誤 → 重試（最多 3 次）
   - API 限流 → 等待後重試
   - 服務不可用 → Fallback 到備用服務

---

### 3.3 任務 T9.3：LangChain Tool 包裝

#### 3.3.1 子任務拆解

| 子任務 | 說明 | 前置條件 | 輸入 | 輸出 |
|--------|------|----------|------|------|
| T9.3.1 | 包裝 Tavily 為 Tool | T9.1 完成 | TavilyClient | `src/langchain/tools/tavily_tool.py` |
| T9.3.2 | 包裝 Web Search 為 Tool | T9.3.1 完成 | web_search 函式 | `src/langchain/tools/search_tool.py` |
| T9.3.3 | 包裝 LLM 呼叫為 Tool | T9.3.2 完成 | call_llm 函式 | `src/langchain/tools/llm_tool.py` |
| T9.3.4 | 建立 Tool 集合與綁定 | T9.3.3 完成 | 各 Tool 定義 | `src/langchain/tools/__init__.py` |

#### 3.3.2 詳細說明

本任務將現有模組包裝為 LangChain 可复用的 Tool：

1. **Tavily Tool**：
   - 使用 `@tool` 裝飾器
   - 輸入：公司名稱、搜尋選項
   - 輸出：搜尋結果與內容摘要

2. **Search Tool**：
   - 封裝傳統的 web_search 函式
   - 作為 Tavily 的備用 Tool

3. **LLM Tool**：
   - 封裝 call_llm 函式
   - 支援 Prompt 輸入與參數配置

4. **Tool 集合**：
   - 建立 Tool 註冊表
   - 支援動態選擇與切換

---

### 3.4 任務 T9.4：品質檢查機制建立

#### 3.4.1 子任務拆解

| 子任務 | 說明 | 前置條件 | 輸入 | 輸出 |
|--------|------|----------|------|------|
| T9.4.1 | 定義品質檢查標準 | T9.3 完成 | 業務需求 | 品質檢查清單 |
| T9.4.2 | 實作品質檢查 Tool | T9.4.1 完成 | 檢查標準 | `src/langchain/tools/quality_check_tool.py` |
| T9.4.3 | 整合至狀態圖 | T9.4.2 完成 | 狀態圖 | 含品質檢查的狀態圖 |
| T9.4.4 | 建立品質報告機制 | T9.4.3 完成 | 檢查結果 | 品質報告模板 |

#### 3.4.2 詳細說明

本任務建立輸出品質驗證機制，確保生成的內容符合品質標準：

1. **品質檢查標準**：
   - 內容長度檢查（是否過短或過長）
   - 關鍵資訊是否存在（公司名稱、產品、服務等）
   - 格式正確性（JSON 結構）
   - 無效內容檢測（是否為預設回應）

2. **品質檢查 Tool**：
   - 自動檢驗輸出內容
   - 回傳檢查結果與建議

3. **狀態圖整合**：
   - 品質檢查節點
   - 失敗時的處理分支

---

### 3.5 任務 T9.5：快取機制實作（可選 - 本階段不做）

> ⚠️ **本階段暫不實作**
> 
> 此為可選優化任務，預留至未來階段執行。

#### 3.5.1 子任務拆解

| 子任務 | 說明 | 前置條件 | 輸入 | 輸出 |
|--------|------|----------|------|------|
| T9.5.1 | 設計快取策略 | T9.2 完成 | 系統需求 | 快取策略設計文件 |
| T9.5.2 | 實作快取層 | T9.5.1 完成 | 策略設計 | `src/langchain/cache.py` |
| T9.5.3 | 整合快取至 Tool | T9.5.2 完成 | 各 Tool | 含快取的 Tool |

#### 3.5.2 詳細說明

本任務為可選任務，旨在減少 API 呼叫次數與成本：

1. **快取策略**：
   - 基於公司名稱的快取鍵
   - 快取過期時間（如 24 小時）
   - 快取大小限制

2. **快取層實作**：
   - 使用 Redis 或本地檔案快取
   - 支援快取讀寫與清除

3. **整合至 Tool**：
   - Tool 呼叫前檢查快取
   - 快取命中時直接回傳

---

### 3.6 任務 T9.6：A/B 測試框架建置（可選 - 本階段不做）

> ⚠️ **本階段暫不實作**
> 
> 此為可選優化任務，預留至未來階段執行。

#### 3.6.1 子任務拆解

| 子任務 | 說明 | 前置條件 | 輸入 | 輸出 |
|--------|------|----------|------|------|
| T9.6.1 | 設計 A/B 測試策略 | T9.4 完成 | 測試需求 | 測試策略設計文件 |
| T9.6.2 | 實作分流機制 | T9.6.1 完成 | 策略設計 | `src/langchain/ab_testing.py` |
| T9.6.3 | 建立指標收集 | T9.6.2 完成 | 分流邏輯 | 指標收集模組 |

#### 3.6.2 詳細說明

本任務為可選任務，支援未來的實驗與優化：

1. **A/B 測試策略**：
   - 不同的 Prompt 模板
   - 不同的模型版本
   - 不同的搜尋策略

2. **分流機制**：
   - 隨機分流或依據用戶特徵
   - 確保實驗一致性

3. **指標收集**：
   - 成功率
   - 回應時間
   - 使用者滿意度

---

## 四、交付物與成果列表

### 4.1 核心交付物

| 交付物編號 | 檔案名稱 | 說明 | 狀態 |
|------------|----------|------|------|
| D9.1 | `src/langchain/__init__.py` | LangChain 模組初始化 | ✅ 已交付 |
| D9.2 | `src/langchain/retry_config.py` | 統一重試配置 | ✅ 已交付 |
| D9.3 | `src/langchain/error_handlers.py` | 錯誤處理包裝器 | ✅ 已交付 |
| D9.4 | `src/langgraph/state.py` | 狀態圖定義 | ✅ 已交付 |
| D9.5 | `src/langgraph/company_brief_graph.py` | 公司簡介生成狀態圖 | ✅ 已交付 |
| D9.6 | `src/langchain/tools/__init__.py` | Tool 集合 | ✅ 已交付 |
| D9.7 | `src/langchain/tools/tavily_tool.py` | Tavily Tool | ✅ 已交付 |
| D9.8 | `src/langchain/tools/search_tool.py` | 搜尋 Tool | ✅ 已交付 |
| D9.9 | `src/langchain/tools/llm_tool.py` | LLM Tool | ✅ 已交付 |
| D9.10 | `src/langchain/tools/quality_check_tool.py` | 品質檢查 Tool | ✅ 已交付 |

### 4.2 可選交付物（本階段不做）

> ⚠️ **預留至未來階段**
> 
> 以下為可選任務的預留交付物，本階段暫不實作：

| 交付物編號 | 檔案名稱 | 說明 | 預計階段 |
|------------|----------|------|----------|
| D9.11 | `src/langchain/cache.py` | 快取機制 | Phase 10+ |
| D9.12 | `src/langchain/ab_testing.py` | A/B 測試框架 | Phase 10+ |

### 4.3 文件交付物

| 交付物編號 | 檔案名稱 | 說明 |
|------------|----------|------|
| D9.13 | `docs/agent_context/phase9_langchain_integration/01_dev_goal_context.md` | 開發目標與背景 |
| D9.14 | `docs/agent_context/phase9_langchain_integration/02_dev_flow_context.md` | 開發流程與時程 |
| D9.15 | `docs/agent_context/phase9_langchain_integration/03_agent_roles_context.md` | Agent 角色定義 |
| D9.16 | `docs/agent_context/phase9_langchain_integration/04_agent_prompts_context.md` | Agent 提示詞 |
| D9.17 | `docs/agent_context/phase9_langchain_integration/05_validation_checklist.md` | 驗證檢查清單 |
| D9.18 | `docs/agent_context/phase9_langchain_integration/06_delivery_record.md` | 交付記錄 |
| D9.19 | `docs/agent_context/phase9_langchain_integration/07_checkpoint_protocol.md` | 檢查點協議 |

---

## 五、檔案命名與存放建議

### 5.1 目錄結構

```
docs/agent_context/phase9_langchain_integration/
├── 01_dev_goal_context.md          # 開發目標與背景
├── 02_dev_flow_context.md          # 開發流程與時程
├── 03_agent_roles_context.md       # Agent 角色定義
├── 04_agent_prompts_context.md     # Agent 提示詞
├── 05_validation_checklist.md      # 驗證檢查清單
├── 06_delivery_record.md           # 交付記錄
├── 07_checkpoint_protocol.md       # 檢查點協議

src/
├── langchain/                      # LangChain 整合模組
│   ├── __init__.py
│   ├── retry_config.py             # 重試配置
│   ├── error_handlers.py           # 錯誤處理
│   ├── cache.py                    # 快取機制（可選）
│   ├── ab_testing.py               # A/B 測試（可選）
│   └── tools/                      # Tool 定義
│       ├── __init__.py
│       ├── tavily_tool.py
│       ├── search_tool.py
│       ├── llm_tool.py
│       └── quality_check_tool.py
│
└── langgraph/                      # LangGraph 狀態圖
    ├── __init__.py
    ├── state.py                    # 狀態定義
    └── company_brief_graph.py      # 公司簡介生成圖
```

### 5.2 命名規範

| 類別 | 規範 | 範例 |
|------|------|------|
| 目錄 | snake_case | `langchain`, `langgraph` |
| 檔案 | snake_case | `tavily_tool.py`, `retry_config.py` |
| 類別 | PascalCase | `TavilyTool`, `CompanyBriefGraph` |
| 函式 | snake_case | `search_company`, `check_quality` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |

---

## 六、驗證檢查清單

### 6.1 功能驗證

- [x] T9.0.1：generate_brief.py 可正確取出 organNo 和 brief
- [x] T9.0.2：prompt_builder.py 可正確接收並組裝所有素材
- [x] T9.0.3：素材傳遞測試通過（包含 organ + organNo + companyUrl + brief + web_content）
- [x] T9.1.1：重試配置模組可正常匯入與使用
- [x] T9.1.2：API 呼叫失敗時自動重試（最多 3 次）
- [x] T9.1.3：主要服務失敗時自動切換至 Fallback
- [x] T9.2.1：狀態圖可正確初始化
- [x] T9.2.2：條件邊可根據輸出結果正確路由
- [x] T9.2.3：錯誤發生時進入正確的處理分支
- [x] T9.3.1：Tavily Tool 可正確執行搜尋
- [x] T9.3.4：所有 Tool 可在 LangChain 環境中使用
- [x] T9.4.2：品質檢查 Tool 可正確驗證輸出
- [x] T9.4.3：品質檢查失敗時可正確觸發重試
- [ ] ~~T9.5.x：快取機制驗證~~ - ⏸️ 本階段不做
- [ ] ~~T9.6.x：A/B 測試框架驗證~~ - ⏸️ 本階段不做

### 6.2 整合驗證

- [ ] 現有的 generate_brief.py 可透過 LangGraph 執行
- [ ] Tavily API 與 Fallback 機制正常運作
- [ ] LLM 呼叫可透過 Tool 執行
- [ ] 日誌可正確記錄狀態圖執行過程

### 6.3 效能驗證

- [ ] 單次請求回應時間不超過 30 秒（無快取）
- [ ] 重試機制不會造成請求逾時
- [ ] 快取機制可減少 API 呼叫次數（可選）

---

## 七、風險與緩解

| 風險 | 發生機率 | 影響程度 | 緩解措施 |
|------|----------|----------|----------|
| LangChain 版本變更 | 中 | 中 | 鎖定版本，漸進升級 |
| LangGraph 狀態圖複雜度過高 | 高 | 中 | 分階段實作，先建立基本流程 |
| Tool 整合導致現有功能回歸 | 中 | 高 | 保留雙軌運行，充分測試 |
| 快取機制導致資料過期 | 低 | 中 | 設定合理的快取過期時間 |

---

## 八、相關文件與資源

### 8.1 內部文件

- `docs/agent_context/phase8_e2e_process_improvement/planning_summary.md` - Phase 8 規劃建議
- `docs/agent_context/phase8_e2e_process_improvement/langchain_langgraph_refactoring_analysis.md` - LangChain/LangGraph 重構分析

### 8.2 外部資源

- [LangChain Retry Documentation](https://python.langchain.com/docs/modules/model_io/chat/retries)
- [LangChain Fallbacks](https://python.langchain.com/docs/modules/model_io/chat/fallbacks)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Tavily API Documentation](https://docs.tavily.com/)

---

*文件資訊*
- 建立日期：2026-04-01
- 專案階段：Phase 9 LangChain 整合
- 依賴技術：LangChain, LangGraph, Python, Tavily API
