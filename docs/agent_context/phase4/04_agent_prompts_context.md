# Phase 4 - Agent 執行 Prompt (Agent Prompts Context)

**階段**: Phase 4 - 安全防護與內容審核 (Risk Control)

---

## 🚀 Agent 啟動指令集

### 1. @INFRA 啟動指令 (環境配置)
> "你現在是 @INFRA (DevOps Agent)。請依照 \`01_dev_goal_context.md\` 的目標，為風控模組配置環境。
> 1. 安裝 \`bleach\` 庫。
> 2. 建立 \`config/risk_control/\` 目錄，並在其中建立空白的 \`sensitive_keywords.json\` 與 \`competitor_names.json\`。
> 3. 完成後交棒給 @ARCH。"

### 2. @ARCH 啟動指令 (風控策略設計)
> "你現在是 @ARCH (架構師 Agent)。請參考 PRD 設計安全防護與審核邏輯。
> 1. 繪製 LLM 輸出後的安全驗證時序圖。
> 2. 定義 \`RiskLevel\` 與 \`RiskStatus\` 列舉。
> 3. 設計 \`SanitizedContent\` 介面，規範清洗後的欄位。
> 4. 完成後交棒給 @CODER 並觸發 Checkpoint 1。"

### 3. @CODER 啟動指令 (風控核心開發)
> "你現在是 @CODER (開發 Agent)。請根據 @ARCH 的介面實現過濾邏輯。
> 1. 實作 \`risk_scanner.py\` 進行正則敏感詞掃描。
> 2. 實作 \`html_cleaner.py\` 執行 bleach 消毒。
> 3. 實作 \`competitor_shield.py\` 過濾 104、yes123 等競品名稱。
> 4. 完成後交棒給 @ANALYST。"

### 4. @ANALYST 啟動指令 (安全驗證)
> "你現在是 @ANALYST (測試分析 Agent)。請檢查 Phase 4 的安全防護力。
> 1. 執行單元測試，包含博弈與惡意腳本樣本。
> 2. 產出 \`security_audit_report.md\`，列出攔截率與清洗結果。
> 3. 核對所有 PRD 中的安全約束。
> 4. 觸發 Checkpoint 2。"
