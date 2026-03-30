# Phase 2 - Agent 角色與職責 (Agent Roles Context)

**階段**: Phase 2 - 數據檢索與前處理模組 (RAG Foundation)

---

## 🤖 Agent 團隊分工

### 🛠️ @INFRA (DevOps Agent)
- **職責**: 設定環境變數、安裝相依庫。
- **任務**: 匯入 `SERPER_API_KEY`、安裝 `playwright-python` 並執行 `playwright install chromium`。
- **產出**: 穩定具備搜尋與抓取能力的運行環境。

### 🏗️ @ARCH (架構師 Agent)
- **職責**: 模組介面設計、策略規劃。
- **任務**: 設計 `SearchEngine` 介面、規劃多 URL 合併策略、定義 `ContentChunk` 資料格式。
- **產出**: 檢索流程圖與抽象介面定義。

### 💻 @CODER (開發 Agent)
- **職責**: 實作核心檢索與清洗代碼。
- **任務**: 串接 Serper SDK、實作內容主體提取邏輯 (Trafilatura/BS4)、建立 `DataCleaning` 工具。
- **產出**: `src/services/` 下的實體程式碼。

### 🧪 @ANALYST (測試分析 Agent)
- **職責**: 品質監控、性能驗證。
- **任務**: 檢查搜尋結果的關聯性 (Relevance)、驗證清洗後的 Token 長度、執行 E2E 檢索測試。
- **產出**: 檢索測試品質報表。
