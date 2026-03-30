# Phase 1 - 同步 MVP Agent 執行 Prompt

**階段**: `phase1_sync_mvp_dev`
**目的**: 提供各 Agent 在實現同步 MVP 過程中的具體執行 Prompt 範例。

## 💬 Agent Prompt 範例

### **@INFRA Prompt**
```
作為 @INFRA，請為「最簡同步 AI 公司簡介生成/優化服務 (MVP)」初始化專案。

參考文件：
- `docs/agent_context/phase1_sync_mvp_dev/01_dev_goal_context.md`
- `docs/agent_context/phase1_sync_mvp_dev/02_dev_flow_context.md`
- `docs/agent_context/phase1_sync_mvp_dev/03_agent_roles_context.md`

任務包括：
1. 建立專案根目錄下的 `src/`, `tests/`, `config/` 目錄。
2. 建立 Python 虛擬環境並激活。
3. 安裝以下 Python 函式庫：`flask` (或 `fastapi`), `requests`, `beautifulsoup4`, `bleach`, `python-dotenv`, `openai` (或 `google-generativeai`), `serper-sdk` (或類似的搜尋 API 客戶端)。
4. 在 `config/` 目錄下建立一個 `.env.example` 文件，包含 `OPENAI_API_KEY`, `GEMINI_API_KEY`, `SERPER_API_KEY` 等佔位符。
5. 報告完成狀態和安裝的依賴列表。
```

### **@ARCH Prompt**
```
作為 @ARCH，請為「最簡同步 AI 公司簡介生成/優化服務 (MVP)」設計核心架構。

參考文件：
- `docs/agent_context/phase1_sync_mvp_dev/01_dev_goal_context.md`
- `docs/agent_context/phase1_sync_mvp_dev/02_dev_flow_context.md`
- `docs/agent_context/phase1_sync_mvp_dev/03_agent_roles_context.md`

參考高階架構規劃：`docs/1111_AI_公司簡介生成模組_高階架構規劃.md`

任務包括：
1. 更新 `docs/mvp_company_profile_api.yml`，確保 `POST /v1/company/profile/process` 端點的請求和響應模型符合同步 MVP 需求，並移除或註解所有非同步相關的定義。
2. 定義以下模組的 Python 類別或函數介面（僅介面，無需實作細節）：
    *   `RequestValidator` (驗證輸入)
    *   `CoreLogicDispatcher` (分派生成/優化邏輯)
    *   `WebSearchService` (呼叫外部搜尋 API)
    *   `WebScraper` (爬取網頁內容)
    *   `TextPreprocessor` (處理文本供 LLM 使用)
    *   `PromptBuilder` (生成和優化模式的 Prompt 構建)
    *   `LLMServiceWrapper` (封裝 LLM 調用)
    *   `PostProcessingModule` (HTML 消毒、內容過濾)
    *   `ResponseFormatter` (格式化最終響應)
    *   `ErrorHandler` (統一錯誤處理)
3. 報告更新後的 OpenAPI 內容和定義的模組介面概要。
```

### **@CODER Prompt**
```
作為 @CODER，請根據 @ARCH 設計的介面，實作「最簡同步 AI 公司簡介生成/優化服務 (MVP)」的所有功能模組。

參考文件：
- `docs/agent_context/phase1_sync_mvp_dev/01_dev_goal_context.md`
- `docs/agent_context/phase1_sync_mvp_dev/02_dev_flow_context.md`
- `docs/agent_context/phase1_sync_mvp_dev/03_agent_roles_context.md`

參考高階架構規劃：`docs/1111_AI_公司簡介生成模組_高階架構規劃.md`

任務包括：
1. 實作 `src/app.py` 作為 API Gateway / Controller，包含 `POST /v1/company/profile/process` 路由。
2. 實作 `RequestValidator` 類別或函數。
3. 實作 `CoreLogicDispatcher` 類別或函數。
4. 實作 `GenerateBriefModule` 及其子模組 (`WebSearchService`, `WebScraper`, `TextPreprocessor`, `PromptBuilder`)。
5. 實作 `OptimizeBriefModule` 及其子模組 (`PromptBuilder`)。
6. 實作 `LLMServiceWrapper`，對接 Gemini 或 OpenAI API。
7. 實作 `PostProcessingModule`，包含 `HTML Sanitizer` (使用 `bleach`) 和 `Content Filter` (基礎敏感詞/競品詞列表)。
8. 實作 `ResponseFormatter`。
9. 實作 `ErrorHandler`，處理常見錯誤並返回標準響應。
10. 報告完成的模組列表和主要功能點。
```

### **@ANALYST Prompt**
```
作為 @ANALYST，請為「最簡同步 AI 公司簡介生成/優化服務 (MVP)」編寫和執行測試。

參考文件：
- `docs/agent_context/phase1_sync_mvp_dev/01_dev_goal_context.md`
- `docs/agent_context/phase1_sync_mvp_dev/02_dev_flow_context.md`
- `docs/agent_context/phase1_sync_mvp_dev/03_agent_roles_context.md`
- `docs/agent_context/phase1_sync_mvp_dev/05_validation_checklist.md`
- `docs/agent_context/phase1_sync_mvp_dev/06_delivery_record.md`
- `docs/agent_context/phase1_sync_mvp_dev/07_checkpoint_protocol.md`

任務包括：
1. 編寫單元測試，覆蓋 `RequestValidator`, `WebScraper`, `TextPreprocessor`, `PostProcessingModule` 等關鍵模組。
2. 編寫整合測試，測試 `POST /v1/company/profile/process` 端點：
    *   測試 GENERATE 模式 (提供 `organ`, `companyUrl`)。
    *   測試 OPTIMIZE 模式 (提供 `organ`, `brief`, `optimization_mode`)。
    *   測試無效輸入 (例如 GENERATE 模式缺少 `companyUrl`)。
    *   測試外部服務失敗 (模擬 Serper.dev 或 LLM 錯誤)。
3. 驗證 LLM 輸出是否符合預期結構 (`body_html`, `summary`, `tags`)。
4. 驗證 HTML 消毒和內容過濾是否有效。
5. 準備一個簡單的 Demo 腳本 (例如使用 `curl` 或 Python `requests`)，展示 GENERATE 和 OPTIMIZE 模式的成功案例。
6. 報告測試結果、覆蓋率和 Demo 步驟。
```