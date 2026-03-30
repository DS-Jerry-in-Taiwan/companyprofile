# Phase 1 - 同步 MVP 驗證清單

**階段**: `phase1_sync_mvp_dev`
**目的**: 確保「最簡同步 AI 公司簡介生成/優化服務 (MVP)」的核心功能按預期工作，並符合基本品質要求。

## ✅ 驗證項目

### **1. API 端點功能驗證**
*   [x] `POST /v1/company/profile/process` 端點可正常響應。
*   [ ] 請求頭中包含 `X-API-Key` 進行驗證 (如果實作)。

### **2. Request Validator 驗證**
*   [x] `mode` 為 `GENERATE` 時，`companyUrl` 必填，否則返回 400 錯誤。
*   [x] `mode` 為 `OPTIMIZE` 時，`brief` 必填，否則返回 400 錯誤。
*   [x] `organNo` 和 `organ` 必填，否則返回 400 錯誤。
*   [x] 其他參數 (例如 `trade`, `word_limit`) 類型正確。

### **3. GENERATE 模式功能驗證**
*   [x] 提供有效 `organ` 和 `companyUrl` 時，能成功生成公司簡介。
*   [x] 網路搜尋服務 (Serper.dev) 調用成功，並返回相關 URL。
*   [x] 網頁爬蟲能從 URL 提取主要文本內容。
*   [x] LLM 能根據提取內容和 Prompt 生成簡介。
*   [x] 外部網路搜尋或 LLM 調用失敗時，API 返回 500 錯誤，並包含清晰的錯誤訊息。

### **4. OPTIMIZE 模式功能驗證**
*   [x] 提供有效 `organ` 和 `brief` 時，能成功優化公司簡介。
*   [x] LLM 能根據 `brief` 和 `optimization_mode` 進行優化。

### **5. 輸出結構與內容驗證**
*   [x] 響應 JSON 包含 `organNo`, `organ`, `body_html`, `summary`, `tags`, `mode` 字段。
*   [x] `body_html` 包含有效的 HTML 內容。
*   [x] `summary` 為簡短摘要。
*   [x] `tags` 為字串陣列。
*   [x] `body_html` 經過 HTML Sanitizer 處理，不包含惡意標籤或屬性。
*   [x] `body_html`, `summary`, `tags` 不包含敏感詞或競品名稱。

### **6. 錯誤處理驗證**
*   [x] 無效請求參數時，返回 `400 Bad Request` 和 `ErrorResponse` 格式。
*   [x] 內部伺服器錯誤時，返回 `500 Internal Server Error` 和 `ServerError` 格式。

### **7. Demo 驗證**
*   [ ] Demo 腳本或工具能成功調用 API，並展示 GENERATE 和 OPTIMIZE 模式的結果。