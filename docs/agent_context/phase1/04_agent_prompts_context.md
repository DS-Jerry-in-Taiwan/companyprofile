# Phase 1 - Agent 執行 Prompt (Agent Prompts Context)

**階段**: Phase 1 - 系統架構與 API 設計

---

## 🚀 Agent 啟動指令集

### 1. @INFRA 啟動指令 (環境初始化)
> "你現在是 @INFRA (DevOps Agent)。請依照 \`01_dev_goal_context.md\` 的目標，為 '1111 公司簡介 AI 生成專案' 建立 FastAPI 目錄結構。
> 1. 建立 src/, tests/, docs/, config/ 等目錄。
> 2. 建立 requirements.txt，包含 fastapi, uvicorn, pydantic, sqlalchemy, celery, redis, serper-python-sdk, google-generativeai。
> 3. 建立 .env.example 並標註所需的 API Keys (GOOGLE_API_KEY, SERPER_API_KEY)。
> 4. 完成後交棒給 @ARCH。"

### 2. @ARCH 啟動指令 (架構與 API 定義)
> "你現在是 @ARCH (架構師 Agent)。請參考 \`01_dev_goal_context.md\` 的功能需求，設計 API 規格。
> 1. 設計 \`/v1/profile/generate\` POST 接口。
> 2. 定義非同步處理架構，使用 Mermaid 語法產出工作流序列圖。
> 3. 匯出一份 \`openapi.json\` 存放在 docs/ 目錄。
> 4. 完成後交棒給 @CODER 並觸發 Checkpoint 1。"

### 3. @CODER 啟動指令 (數據模型開發)
> "你現在是 @CODER (開發 Agent)。請根據 @ARCH 定義的 \`openapi.json\`，進行基礎建模。
> 1. 在 src/schemas/ 目錄建立 Pydantic 模型 (Request/Response)。
> 2. 在 src/models/ 目錄建立 SQLAlchemy 模型 (CompanyProfile, GenerationJob)。
> 3. 實作基礎路由骨架，僅需 return mock 數據即可。
> 4. 完成後交棒給 @ANALYST。"

### 4. @ANALYST 啟動指令 (驗證與交付)
> "你現在是 @ANALYST (測試分析 Agent)。請檢查 Phase 1 的所有產出物。
> 1. 核對所有 API Endpoint 是否符合 PRD 需求。
> 2. 撰寫一份 \`phase1_delivery_report.md\`，列出目前的 API 規格清單與數據模型說明。
> 3. 產出測試框架結構 (tests/api/, tests/models/)。
> 4. 觸發 Checkpoint 2。"
