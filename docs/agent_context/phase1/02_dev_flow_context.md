# Phase 1 - 同步 MVP 開發流程

**階段**: `phase1_sync_mvp_dev`
**目的**: 依據高階模組架構，規劃具體的開發步驟與 Agent 分工。

## 📋 執行流程

### **Phase 1.1 - 環境與基礎設定 (@INFRA) - 已完成**
1.  **專案初始化**: 已建立專案目錄結構，設定 Python 虛擬環境。
2.  **依賴安裝**: 已安裝必要的函式庫 (flask, pytest, requests, beautifulsoup4, bleach, pydantic, google-generativeai, python-dotenv)。
3.  **配置管理**: 已建立 `.env.example` 檔案。

### **Phase 1.2 - 架構與介面設計 (@ARCH) - 已完成 (Checkpoint 1 通過)**
1.  **API 介面定義**:
    *   已更新 `docs/mvp_company_profile_api.yml`，明確定義 `POST /v1/company/profile/process` 的請求與響應模型。
    *   已移除或註解非同步相關的端點。
2.  **模組介面定義**:
    *   已定義各模組 (例如 `Request Validator`, `Web Search Service`, `LLM Service Wrapper`) 的類別或函數介面，並記錄於 `docs/phase1_sync_arch_interface.md`。
3.  **錯誤處理機制設計**: 已規劃統一的錯誤響應格式和錯誤類型。

### **Phase 1.3 - 核心功能實作 (@CODER) - 已完成**
1.  **API Gateway / Controller 實作**: 已建立 Flask 應用，定義 `POST /v1/company/profile/process` 路由 (`src/functions/api_controller.py`)。
2.  **Request Validator 實作**: 已實作輸入參數驗證 (`src/functions/utils/request_validator.py`)。
3.  **Core Logic Dispatcher 實作**: 已實作邏輯分派 (`src/functions/utils/core_dispatcher.py`)。
4.  **Generate Brief Module 實作**:
    *   **Web Search Service**: 已實作呼叫 Serper.dev API 獲取 URL。
    *   **Web Scraper / Content Extractor**: 已實作使用 `requests` 和 `BeautifulSoup` 爬取網頁並提取主要文本。
    *   **Text Preprocessor**: 已實作清洗、合併、摘要文本。
    *   **Prompt Builder (Generate)**: 已實作構建生成模式的 LLM Prompt。
5.  **Optimize Brief Module 實作**:
    *   **Prompt Builder (Optimize)**: 已實作構建優化模式的 LLM Prompt。
6.  **LLM Service Wrapper 實作**: 已實作封裝 LLM API 調用 (`src/functions/utils/llm_service.py`)。
7.  **Post-processing Module 實作**:
    *   **HTML Sanitizer**: 已實作使用 `bleach` 清理 HTML。
    *   **Content Filter**: 已實作基礎敏感詞和競品詞過濾 (`src/functions/utils/post_processing.py`)。
8.  **Response Formatter 實作**: 已實作將結果格式化為 `CompanyProfileResponse` (`src/functions/utils/response_formatter.py`)。
9.  **Error Handler 實作**: 已實作集中處理應用程式錯誤 (`src/functions/utils/error_handler.py`)。

### **Phase 1.4 - 測試與驗證 (@ANALYST) - 進行中**
1.  **單元測試**: 已為各個模組編寫單元測試。
2.  **整合測試**: 已測試 `POST /v1/company/profile/process` 端點，覆蓋 GENERATE 和 OPTIMIZE 模式，並修正測試不穩定問題。
3.  **功能驗證**:
    *   已使用真實 `companyUrl` 測試 GENERATE 模式。
    *   已使用不同 `brief` 和 `optimization_mode` 測試 OPTIMIZE 模式。
    *   已驗證 HTML 消毒和內容過濾是否生效。
4.  **Demo 準備**: 準備一個簡單的腳本或 Postman 集合，用於展示 API 功能。
5.  **最終交付確認**: 準備觸發 Checkpoint 2。

## 📊 時間估算
*   **總計**: 預計 2-3 個工作天完成 MVP 核心功能。