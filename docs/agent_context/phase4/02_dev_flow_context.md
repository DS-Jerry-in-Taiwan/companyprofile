# Phase 4 - 開發流程與步驟 (Dev Flow Context)

**階段**: Phase 4 - 安全防護與內容審核 (Risk Control)
**更新時間**: 2026-03-27

---

## 🚀 開發執行流程

### Step 1: 安全組件整合與配置 (INFRA)
- 安裝 `bleach` 等 HTML 清理工具。
- 準備敏感詞庫 (JSON/YAML) 的本地存儲配置。

### Step 2: 風控引擎介面設計 (ARCH)
- 定義 `RiskControl` 介面，包括關鍵字掃描、競品檢查、HTML 清洗。
- 規劃「審核狀態機」 (如: PENDING, APPROVED, REJECTED)。
- 繪製 LLM 輸出後的安全驗證時序圖。

### Step 3: 風控服務核心開發 (CODER)
- 實作 `risk_control_service.py`：使用 Regex 高效掃描黑名單。
- 實作 `competitor_filter.py`：實現競品名稱屏蔽邏輯。
- 實作 `html_sanitizer.py`：利用 bleach 進行標籤白名單過濾。

### Step 4: 測試與合規驗證 (ANALYST)
- 建立負面測試案例 (包含敏感詞與惡意腳本的測試樣本)。
- 驗證過濾邏輯的準確率 (False Positive 檢查)。
- 觸發 Checkpoint 2 確認最終交付。

---

## ⏳ 時間估算與里程碑
- **Step 1-2**: 預計耗時 1 小時 (INFRA + ARCH)。
- **Step 3**: 預計耗時 3 小時 (CODER)。
- **Step 4**: 預計耗時 1 小時 (ANALYST)。
