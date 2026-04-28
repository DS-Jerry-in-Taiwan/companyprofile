# Phase 3 - 開發流程與步驟 (Dev Flow Context)

**階段**: Phase 3 - AI/LLM 核心邏輯與 Prompt 工程
**更新時間**: 2026-03-27

---

## 🚀 開發執行流程

### Step 1: LLM API 整合與配置 (INFRA)
- 在環境變數設定 `GOOGLE_API_KEY` 或 `OPENAI_API_KEY`。
- 安裝 LLM SDK (如 `google-generativeai` 或 `openai`)。

### Step 2: Prompt 工程策略設計 (ARCH)
- 針對「生成模式」設計 Initial Prompt 與 Few-Shot 範例。
- 針對「優化模式」設計 Refine Prompt 與編輯指令。
- 規劃 Token 計數與壓縮策略。

### Step 3: LLM 服務核心開發 (CODER)
- 實作 `llm_service.py`：封裝 LLM API 調用，處理 Prompt 注入、參數設定、錯誤重試。
- 實作 `token_manager.py`：負責 Token 計數與內容截斷/摘要。
- 整合 Phase 2 的 `CleanedData` 到 Prompt 中。

### Step 4: 測試與品質評估 (ANALYST)
- 撰寫測試案例，驗證「生成」與「優化」模式的輸出品質。
- 評估 LLM 輸出的準確性、語氣、長度與格式。
- 執行成本與延遲監控。

---

## ⏳ 時間估算與里程碑
- **Step 1-2**: 預計耗時 1 小時 (INFRA + ARCH)。
- **Step 3**: 預計耗時 3 小時 (CODER)。
- **Step 4**: 預計耗時 1.5 小時 (ANALYST)。
