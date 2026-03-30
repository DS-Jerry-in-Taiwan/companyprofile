# Phase 5 - Agent 執行 Prompt (Agent Prompts Context)

**階段**: Phase 5 - 最終測試、優化與交付

---

## 🚀 Agent 啟動指令集

### 1. @INFRA 啟動指令 (監控與樣本準備)
> "你現在是 @INFRA (DevOps Agent)。請依照 \`01_dev_goal_context.md\` 的目標，準備測試環境。
> 1. 建立 \`data/test_samples/\` 目錄，存放不同規模企業的測試清單。
> 2. 撰寫一個簡單的效能計時工具，統計 API 每個環節的耗時。
> 3. 完成後交棒給 @ANALYST。"

### 2. @ANALYST 啟動指令 (規模化測試)
> "你現在是 @ANALYST (測試分析 Agent)。請進行最終的品質評量。
> 1. 執行 \`scripts/batch_test.py\` (需先實作)，針對 20 個樣本產出生成結果。
> 2. 比對搜尋到的原始事實與生成內容，標註可能的「幻覺 (Hallucination)」。
> 3. 產出一份 \`final_quality_report.md\`，包含準確性、語氣與合規性的評分。
> 4. 完成後交棒給 @CODER 並觸發 Checkpoint 1。"

### 3. @CODER 啟動指令 (細節修正)
> "你現在是 @CODER (開發 Agent)。請根據 @ANALYST 的測試反饋優化代碼。
> 1. 針對內容過短或格式不整齊的公司，調整 Prompt 注入邏輯或模型參數。
> 2. 清理代碼中的冗餘日誌，確保代碼具備生產環境品質。
> 3. 修復目前發現的所有 Bug。
> 4. 完成後交棒給 @ARCH。"

### 4. @ARCH 啟動指令 (交付與文檔)
> "你現在是 @ARCH (架構師 Agent)。請完成最終的專案交付與結案。
> 1. 更新 \`README.md\`，包含系統架構圖、安裝指南與 API 文件。
> 2. 核對 Phase 1-5 的所有驗證清單，確認需求 100% 達成。
> 3. 撰寫最終交付報告 \`final_delivery_summary.md\`。
> 4. 觸發 Checkpoint 2。"
