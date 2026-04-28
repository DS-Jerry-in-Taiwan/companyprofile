# Phase 1 - 同步 MVP Agent 角色與職責

**階段**: `phase1_sync_mvp_dev`
**目的**: 明確各 Agent 在實現同步 MVP 過程中的具體職責。

## 👨‍💻 Agent 角色定義

### **@INFRA (基礎設施工程師)**
*   **職責**: 負責專案的環境設定、依賴管理和基礎配置。
*   **任務**:
    *   初始化專案目錄結構。
    *   安裝所有必要的 Python 函式庫。
    *   設定環境變數和 API Keys。

### **@ARCH (架構師)**
*   **職責**: 負責定義 API 介面、模組介面和數據模型，確保架構清晰、可擴展。
*   **任務**:
    *   更新 OpenAPI 規格文件 (`mvp_company_profile_api.yml`)，定義同步 API。
    *   設計各個模組 (例如 `Request Validator`, `Web Search Service`, `LLM Service Wrapper`) 的介面和數據流。
    *   規劃錯誤處理的結構。

### **@CODER (程式開發者)**
*   **職責**: 負責根據架構設計，實作所有功能模組的程式碼。
*   **任務**:
    *   編寫 API Controller、Request Validator、Core Logic Dispatcher。
    *   實作 Generate Brief Module 和 Optimize Brief Module 的所有子模組。
    *   實作 LLM Service Wrapper 和 Post-processing Module。

### **@ANALYST (測試與分析師)**
*   **職責**: 負責編寫和執行測試，驗證功能正確性、數據品質和合規性。
*   **任務**:
    *   編寫單元測試和整合測試。
    *   執行功能測試，驗證 GENERATE 和 OPTIMIZE 模式的輸出。
    *   檢查 HTML 消毒和內容過濾是否按預期工作。
    *   準備 Demo 腳本。