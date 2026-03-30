# Phase 3 - Agent 角色與職責 (Agent Roles Context)

**階段**: Phase 3 - AI/LLM 核心邏輯與 Prompt 工程

---

## 🤖 Agent 團隊分工

### 🛠️ @INFRA (DevOps Agent)
- **職責**: 配置 LLM 相關的環境變數與 SDK。
- **任務**: 確保 `GOOGLE_API_KEY` 或 `OPENAI_API_KEY` 正確載入，安裝必要的 Python 套件。
- **產出**: 具備 LLM 調用能力的運行環境。

### 🏗️ @ARCH (架構師 Agent)
- **職責**: Prompt 策略與 Token 管理設計。
- **任務**: 設計兩種模式 (生成/優化) 的 Prompt 範本，規劃 Token 壓縮策略，定義 LLM 輸出的 Pydantic Schema。
- **產出**: Prompt 範本文件、Token 管理策略、LLM Output Schema。

### 💻 @CODER (開發 Agent)
- **職責**: 實作 LLM 服務核心程式。
- **任務**: 封裝 LLM SDK、實現 Prompt 填充邏輯、實作 Token 計數與內容調整。
- **產出**: `src/services/llm_service.py` 及相關輔助工具。

### 🧪 @ANALYST (測試分析 Agent)
- **職責**: 評估 LLM 輸出品質、進行 Prompt A/B 測試。
- **任務**: 設計多樣化的測試案例（知名公司、新創公司、不同產業），評估輸出內容的相關性、準確性與語氣。
- **產出**: LLM 輸出品質評估報告。
