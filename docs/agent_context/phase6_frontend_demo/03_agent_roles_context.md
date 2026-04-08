# Phase 6 - Agent 角色

**階段**: `phase6_frontend_demo`

---

## 🤖 Agent 角色定義

| Agent | 角色 | 職責 |
|-------|------|------|
| **@INFRA** | 環境建置 | 前端專案初始化、依賴安裝 |
| **@ARCH** | 架構設計 | Schema 擴展、API 設計、前端架構規劃 |
| **@CODER** | 程式實現 | Vue 元件、表單、API 整合 |
| **@ANALYST** | 測試驗證 | 端到端測試、RWD 測試 |

---

## 📋 詳細職責

### @INFRA - 環境建置

**主要任務**:
- 建立 `frontend/` 目錄結構
- 初始化 Vue 3 + Vite 專案
- 安裝 Tailwind CSS
- 配置 API 代理（指向本地 Flask）

**交付物**:
```
frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── index.html
└── src/
    └── main.js
```

---

### @ARCH - 架構設計

**主要任務**:
- 擴展 Input Schema 支援新欄位
- 設計前端表單結構
- 定義元件介面
- 更新 API 文件

**交付物**:
- `docs/api_schema_v2.md`
- 前端架構圖

---

### @CODER - 程式實現

**主要任務**:
- 實作 Vue 元件
- 實作表單驗證
- 實作 API 呼叫
- 實作結果顯示

**交付物**:
```
frontend/src/
├── App.vue
├── api.js
├── components/
│   ├── BriefForm.vue
│   ├── ResultPanel.vue
│   └── RiskAlert.vue
└── styles/
    └── main.css
```

---

### @ANALYST - 測試驗證

**主要任務**:
- 功能測試
- 整合測試
- RWD 測試
- 報告產出

**交付物**:
- 測試報告
- Bug 清單（如有）
