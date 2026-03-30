# Phase 3 - Agent 執行 Prompt (Agent Prompts Context)

**階段**: Phase 3 - AI/LLM 核心邏輯與 Prompt 工程

---

## 🚀 Agent 啟動指令集

### 1. @INFRA 啟動指令 (環境配置)
> "你現在是 @INFRA (DevOps Agent)。請依照 `01_dev_goal_context.md`，為 LLM 模組配置環境。
> 1. 更新 `.env` 加入 `GOOGLE_API_KEY` 或 `OPENAI_API_KEY` (暫用 dummy 值)。
> 2. 安裝 `google-generativeai` 或 `openai` SDK。
> 3. 確認 LLM 基礎連線功能。
> 4. 完成後交棒給 @ARCH。"

### 2. @ARCH 啟動指令 (Prompt 設計)
> "你現在是 @ARCH (架構師 Agent)。請參考 `01_dev_goal_context.md` 設計 LLM 相關邏輯。
> 1. 設計 `generate_prompt_template.txt` 與 `optimize_prompt_template.txt`。
> 2. 規劃 Token 計數與壓縮的策略，並繪製流程圖 (Mermaid)。
> 3. 設計 `LLMOutput` Pydantic 模型 (包含 title, body_html, summary)。
> 4. 完成後交棒給 @CODER 並觸發 Checkpoint 1。"

### 3. @CODER 啟動指令 (核心開發)
> "你現在是 @CODER (開發 Agent)。請根據 @ARCH 的設計實現功能。
> 1. 實作 `llm_service.py` (封裝 LLM API 調用，處理 Prompt 填充)。
> 2. 實作 `token_manager.py` (處理 Token 計數與內容截斷)。
> 3. 整合 Phase 2 的 `CleanedData` 到 Prompt 中。
> 4. 完成後交棒給 @ANALYST。"

### 4. @ANALYST 啟動指令 (驗證分析)
> "你現在是 @ANALYST (測試分析 Agent)。請檢查 Phase 3 的 LLM 輸出品質。
> 1. 撰寫測試案例以確認「生成」與「優化」模式的輸出內容。
> 2. 評估輸出內容的相關性、準確性與語氣。
> 3. 觸發 Checkpoint 2。"
