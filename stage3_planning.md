# Phase 14 Stage 3 Planning

## Goal
整合 Gemini/Tavily 混合搜尋模組到主流程，並進行整合驗證。

## Instructions
- 嚴格遵循「設計 -> 實作 -> 測試 -> 評估 -> 改進」的循環
- 使用配置驅動方式，讓主流程透過參數調用不同搜尋策略
- 測試區驗證後再遷移到正式專案路徑
- 更新 Phase14 開發文件和 README

## Discoveries
### 1. 搜尋工具層架構
- 三種策略：Tavily 批次、Gemini Few-shot、Gemini 規劃 + Tavily
- Gemini Few-shot 資訊最完整（JSON 格式），但速度較慢（5-30s）
- Tavily 批次快速（約 1s），但資訊量較少

### 2. 配置驅動流程
```
config/search_config.json (provider: "gemini_fewshot")
    ↓
ConfigDrivenSearchTool
    ↓
SearchToolFactory → 根據 provider 創建工具
    ↓
返回 SearchResult
```

### 3. 主流程整合位置
- `src/langgraph_state/company_brief_graph.py` 的 `search_node()` 函式
- 原本使用 `tavily_client.search_and_extract()`，現已替換為 `config_driven_search.search()`

### 4. 前端驗證問題
- 前端頁面正常載入，word_limit 欄位已移除
- 三模板選擇（CONCISE/STANDARD/DETAILED）正常顯示
- 填寫表單後點擊「生成簡介」，等待超過 60 秒無回應
- 可能原因：API Gateway 配置問題或 API 端點未正確設定

## Accomplished
### 已完成
✅ 測試區實作搜尋工具層（`scripts/stage3_test/search_tools.py`）
✅ 配置驅動搜尋實作（`scripts/stage3_test/config_driven_search.py`）
✅ 遷移到正式區（`src/services/search_tools.py`、`src/services/config_driven_search.py`）
✅ 主流程整合（`src/langgraph_state/company_brief_graph.py` 的 `search_node()`）
✅ Phase14 文檔更新（`stage3_planning.md`、`PROGRESS_TRACKING.md`、`06_delivery_record.md`、`02_dev_flow_context.md`）
✅ 程式碼註解更新
✅ README.md 更新（架構圖改為 Mermaid 格式）
✅ 修復 `WordCountValidationResult` import 問題

### 進行中
⏳ 前端整合驗證 - 點擊「生成簡介」後 API 無回應

## Next Steps
1. **排查前端 API 無回應問題**
   - 檢查後端 API 是否正常運行
   - 確認 API Gateway 配置
   - 檢查前端 `/api/v1` 端點設定

2. **完成前端整合驗證**
   - 測試 CONCISE/STANDARD/DETAILED 三種模式
   - 驗證輸出格式和字數