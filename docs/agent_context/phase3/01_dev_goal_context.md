# Phase 3 - 開發目標與需求 (Dev Goal Context)

**階段**: Phase 3 - AI/LLM 核心邏輯與 Prompt 工程
**目的**: 設計並實作 LLM 的 Prompt 策略，以產出高質量、符合規範的公司簡介。

## 🎯 開發目標
- 設計並實作 **「生成模式」** 與 **「優化模式」** 的 Prompt 範本。
- 處理 **Long Context** 的截斷與壓縮策略，優化 Token 使用效率。
- 實作 **結構化輸出控制**，確保 LLM 回傳 JSON 格式的資料。
- 導入 **Temperature** 等參數調優，平衡創造性與穩定性。

## 📋 功能需求概要
1. **Prompt 範本管理**: 能夠動態調整或切換 Prompt 範本。
2. **Context 整合**: 將 Phase 2 獲取的清洗後數據 (CleanedData) 注入 Prompt。
3. **LLM 調用器**: 封裝 LLM API 調用邏輯，處理重試與錯誤。
4. **輸出格式規範**: 強制 LLM 輸出為定義好的 JSON 結構，包含 `title`, `body_html`, `summary`。

## ✅ 驗收標準 (Acceptance Criteria)
- 產出 `src/services/llm_service.py` 且通過 Mock 測試。
- 能夠在「生成模式」下，僅憑公司名稱產出基礎簡介。
- 能夠在「優化模式」下，對現有簡介進行合理擴展。
- LLM 輸出符合定義的 JSON Schema。
- 完成 Prompt 實驗記錄與初步評估。
