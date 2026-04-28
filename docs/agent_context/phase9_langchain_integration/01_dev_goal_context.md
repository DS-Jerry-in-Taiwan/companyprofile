# Phase 9 開發目標與背景

## 一、階段背景

### 1.1 承接 Phase 8

Phase 8 已完成以下工作：

1. **問題診斷**：確認直接爬蟲容易被阻擋、錯誤處理分散、無 Fallback 機制
2. **方案選擇**：選擇 LangChain + Tavily API 作為解決方案
3. **實作完成**：
   - Tavily API 服務提供者 (`src/services/tavily_search.py`)
   - Tavily Client (`src/functions/utils/tavily_client.py`)
   - generate_brief.py 改用 Tavily 替代爬蟲
4. **待完成**：短期需設定 TAVILY_API_KEY 並完整測試

### 1.2 本階段動機

Phase 8 解決了爬蟲被阻擋的問題，但還存在以下不足：

| 面向 | 問題 | 影響 |
|------|------|------|
| 錯誤處理 | 錯誤處理分散在各模組，缺乏統一配置 | 維護困難，異常時無法統一降級 |
| 動態路由 | 流程固定，無法根據結果動態調整 | 缺乏彈性，錯誤時只能拋出例外 |
| 可複用性 | 各模組獨立運作，無法在 Agent 環境複用 | 重複開發，難以擴展 |
| 品質保證 | 生成結果缺乏品質檢驗機制 | 可能輸出無效內容 |

### 1.3 技術動機

LangChain 與 LangGraph 提供：

1. **宣告式錯誤處理**：`RunnableRetry` + `RunnableWithFallbacks` 可用配置方式定義重試與降級策略
2. **動態流程控制**：LangGraph 條件邊可根據執行結果動態路由
3. **Tool 生態**：將現有模組包裝為 Tool，可在各種 Agent 框架中複用
4. **狀態管理**：自動追蹤圖形執行狀態，方便偵錯與監控

---

## 二、階段目標

### 2.1 主要目標

| 目標 | 說明 | 成功指標 |
|------|------|----------|
| 錯誤處理整合 | 統一的重試與 Fallback 機制 | 所有 API 呼叫具備相關機制 |
| 動態路由 | LangGraph 條件邊實現動態路由 | 可根據錯誤類型選擇處理路徑 |
| 工具化 | 將現有模組包裝為 LangChain Tool | 可在 Agent 環境複用 |
| 品質檢查 | 建立輸出品質驗證機制 | 生成結果通過率 > 95% |

### 2.2 可選目標

| 目標 | 說明 | 成功指標 |
|------|------|----------|
| 快取機制 | 減少重複 API 呼叫 | API 呼叫次數減少 30% |
| A/B 測試 | 支援不同策略的實驗比較 | 可比較不同策略的效果 |

---

## 三、成功標準

### 3.1 功能標準

- [ ] 所有 API 呼叫具備重試機制（預設最多 3 次）
- [ ] 主要服務失敗時自動 Fallback 至備用服務
- [ ] LangGraph 狀態圖可正確執行公司簡介生成流程
- [ ] 條件邊可根據搜尋結果選擇後續處理路徑
- [ ] 各 Tool 可在 LangChain 環境中正確執行
- [ ] 品質檢查 Tool 可驗證輸出內容

### 3.2 整合標準

- [ ] generate_brief.py 可透過 LangGraph 執行
- [ ] Tavily API 與 Fallback 機制正常運作
- [ ] LLM 呼叫可透過 Tool 執行
- [ ] 日誌可正確記錄狀態圖執行過程

### 3.3 效能標準

- [ ] 單次請求回應時間不超過 30 秒（無快取）
- [ ] 重試機制不會造成請求逾時
- [ ] 快取機制可減少 API 呼叫次數（可選）

---

## 四、相關文件

### 4.1 階段文件

- `docs/agent_context/phase9_langchain_integration/planning_summary.md` - 本階段規劃總結
- `docs/agent_context/phase9_langchain_integration/02_dev_flow_context.md` - 開發流程與時程

### 4.2 參考文件

- `docs/agent_context/phase8_e2e_process_improvement/planning_summary.md` - Phase 8 規劃建議
- `docs/agent_context/phase8_e2e_process_improvement/langchain_langgraph_refactoring_analysis.md` - LangChain/LangGraph 重構分析

---

*文件資訊*
- 建立日期：2026-04-01
- 專案階段：Phase 9 LangChain 整合
- 文档类型：开发目标与背景
