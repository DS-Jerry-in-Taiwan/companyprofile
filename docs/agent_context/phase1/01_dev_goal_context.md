# Phase 1 - 同步 MVP 開發目標

**階段**: `phase1_sync_mvp_dev`
**目的**: 實現「最簡同步 AI 公司簡介生成/優化服務 (MVP)」的核心功能，打通端到端流程，以便快速驗證與 Demo。

## 🎯 開發目標

1.  **實現單一同步 API 端點**: `POST /v1/company/profile/process`，能夠接收生成或優化請求。
2.  **整合生成模式 (GENERATE)**:
    *   根據 `organ` 和 `companyUrl` 進行即時網路搜尋 (RAG)。
    *   從搜尋結果中提取網頁內容。
    *   使用 LLM 根據提取內容生成公司簡介。
3.  **整合優化模式 (OPTIMIZE)**:
    *   根據提供的 `brief` 和其他參數，使用 LLM 優化公司簡介。
4.  **實作內容後處理**: 包含 HTML 消毒 (`bleach`) 和基礎敏感詞過濾。
5.  **提供結構化輸出**: LLM 輸出應包含 `body_html`, `summary`, `tags`。
6.  **基本錯誤處理**: 針對輸入驗證失敗、外部服務調用失敗等情況提供清晰的錯誤響應。

## 🚀 產出物 (Deliverables)

*   一個可運行的 API 服務，提供 `POST /v1/company/profile/process` 端點。
*   相關的程式碼模組，實現上述功能。
*   一份更新後的 OpenAPI 規格文件，反映同步 API。
*   一份 Demo 腳本或簡單的客戶端調用範例。