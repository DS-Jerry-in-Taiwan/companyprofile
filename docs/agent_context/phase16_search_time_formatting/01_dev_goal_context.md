# Phase 16 - 搜尋時格式化優化

## 階段概述

**階段名稱**: Phase 16 - 搜尋時格式化優化
**版本**: v1.0.0
**執行日期**: 2026-04-15
**預計耗時**: 3-5 天
**執行模式**: 分階段驗證（設計 → 開發 → 測試 → 文件）
**當前狀態**: 規劃中

---

## 目標

將搜尋結果格式化的職責從 `summary_node`（後處理）前移到 `search_node`（搜尋時），使搜尋 LLM 直接返回結構化資料，進而：

1. **提升品質**：搜尋 LLM 做第一次整合，去除冗餘和雜訊
2. **簡化流程**：`summary_node` 從「合併文字」改為「合併結構」
3. **提高效率**：Generate 拿到乾淨的結構化輸入

---

## 核心改變

### 目前流程（Phase 15）

```
搜尋 → 搜尋結果（純文字）
    ↓
summary_node → 純文字拼接 → aspect_summaries
    ↓
generate_node → 對文字理解 → 生成簡介
```

### 優化後流程（Phase 16）

```
搜尋（prompt 要求結構化輸出）→ 搜尋結果（JSON 結構）
    ↓
summary_node → 合併結構化資料 → aspect_summaries（已結構化）
    ↓
generate_node → 對結構理解 → 生成簡介
```

---

## 開發邊界

### ✅ 涵蓋範圍

1. **搜尋 Prompt 優化**：加入結構化輸出要求
   - 要求搜尋 LLM 返回 JSON 格式
   - 定義四面向的欄位結構

2. **搜尋結果解析**：處理新的結構化格式
   - JSON 解析
   - 格式驗證
   - Fallback 處理

3. **Summary Node 更新**：改為合併結構化資料
   - 從純文字拼接改為結構合併
   - 去重邏輯（可選）
   - 長度控制（可選）

4. **文件更新**：context 和實作文件

5. **測試驗證**：
   - 搜尋結果格式檢驗
   - Generate 輸入品質測試
   - 端到端測試

### ❌ 不涵蓋範圍

1. **Generate 邏輯調整**：`generate_node` 本身不改
   - 仍然使用目前的 prompt template
   - 只是輸入格式變了（從純文字變結構化）

2. **新 Provider 開發**：不涉及搜尋策略本身
   - `tavily`, `gemini_fewshot`, `gemini_planner_tavily` 都保留
   - 只是各自的 prompt 加上格式化要求

3. **UI/UX 改變**：不涉及前端
   - 後端輸出格式不變（仍是 `aspect_summaries`）
   - 前端無需改動

4. **監控可視化**：不新增監控維度
   - 沿用 Phase 15 的 log 機制

---

## 工項清單

| # | 工項 | 檔案 | 複雜度 | 估時 |
|---|------|------|--------|------|
| 1 | 設計搜尋 prompt 結構化格式 | 設計文件 | 低 | 0.5 天 |
| 2 | 更新 `GeminiFewShotSearchTool` prompt | `search_tools.py` | 中 | 1 天 |
| 3 | 更新 `GeminiPlannerTavilyTool` prompt | `search_tools.py` | 中 | 1 天 |
| 4 | 更新 `summary_node` 的合併邏輯 | `company_brief_graph.py` | 中 | 1 天 |
| 5 | 測試驗證（搜尋結果 + Generate 輸入） | 測試代碼 | 高 | 1 天 |
| 6 | 文件更新 | context 文件 | 低 | 0.5 天 |

**總計**: 3-5 天

---

## 開發與測試步驟

### Step 1: 設計階段（0.5 天）

**輸出物**：搜尋 prompt 結構化格式定義

```json
{
  "foundation": {
    "type": "string",
    "description": "品牌實力與基本資料",
    "max_length": 500
  },
  "core": {
    "type": "string",
    "description": "技術產品與服務核心",
    "max_length": 500
  },
  "vibe": {
    "type": "string",
    "description": "職場環境與企業文化",
    "max_length": 500
  },
  "future": {
    "type": "string",
    "description": "近期動態與未來展望",
    "max_length": 500
  }
}
```

**驗證**：確認四個面向的定義明確、無歧義

### Step 2: 搜尋 Prompt 優化（2 天）

**工項 2**: `GeminiFewShotSearchTool`
- 修改 `GEMINI_PROMPT_TEMPLATE`，加入結構化要求
- 驗證：搜尋結果能否正確解析為 JSON

**工項 3**: `GeminiPlannerTavilyTool`
- 修改 `GEMINI_PLANNER_PROMPT`，加入結構化要求
- 驗證：Gemini 規劃結果、Tavily 執行結果都能符合結構

### Step 3: Summary Node 更新（1 天）

**工項 4**: 合併邏輯改為結構化
- 不再純文字拼接
- 改為將每個面向的結構化資料合併
- 示意：
  ```python
  # 舊邏輯
  combined_content = "\n\n".join([result["answer"] for result in queries])
  
  # 新邏輯
  # 每個面向已經是結構化的（foundation/core/vibe/future），直接合併
  ```

### Step 4: 測試驗證（1 天）

**測試 1**: 搜尋結果格式檢驗
```bash
test_search_result_json_format.py
- 驗證 gemini_fewshot 返回有效 JSON
- 驗證 gemini_planner_tavily 返回有效 JSON
- 驗證缺失欄位的 fallback
```

**測試 2**: Generate 輸入品質測試
```bash
test_generate_input_quality.py
- 驗證 generate_node 收到結構化輸入
- 驗證生成質量與舊方式對比
- 端到端流程測試
```

**驗證清單**：
- [ ] 所有搜尋 provider 都返回結構化結果
- [ ] Summary node 能正確合併結構化資料
- [ ] Generate node 輸入品質 ≥ Phase 15（或更好）
- [ ] 無 backward compatibility 問題

### Step 5: 文件更新（0.5 天）

- 更新 `01_dev_goal_context.md`
- 更新 `02_dev_flow_context.md`
- 新增 `design_spec.md`（搜尋 prompt 設計文件）

---

## 成功標準

| # | 標準 | 驗證方式 |
|---|------|----------|
| 1 | 搜尋結果都是結構化 JSON | 搜尋 50 個公司，100% 返回有效 JSON |
| 2 | Summary node 能正確合併 | 對比舊方式輸出，無回歸 |
| 3 | Generate 品質不下降 | 對比測試集，生成內容質量評分 ≥ Phase 15 |
| 4 | 無硬編碼模型名稱 | 代碼檢查，所有模型配置來自 config |
| 5 | 文件完整 | Phase 16 context 文件齊全 |

---

## 注意事項

1. **Backward Compatibility**
   - `summary_node` 的輸出格式不變（仍是 `aspect_summaries`）
   - `generate_node` 輸入格式改變（從純文字變結構化），但 prompt 不變
   - API 層無需改動

2. **成本增加**
   - 搜尋 prompt 變長 → token 增加 ~10-15%
   - 可接受的額外成本

3. **Fallback 機制**
   - 如果 JSON 解析失敗，fallback 到純文字模式
   - 確保系統穩定性

4. **測試環境**
   - 使用實際搜尋結果測試（不用 mock）
   - 需要 GEMINI_API_KEY 和 TAVILY_API_KEY

---

## 下一步

當此文件通過審核後，Development Agent 將按照以下順序執行：
1. 設計搜尋 prompt 結構化格式
2. 實作 Prompt 優化
3. 實作 Summary Node 更新
4. 執行測試驗證
5. 更新文件
