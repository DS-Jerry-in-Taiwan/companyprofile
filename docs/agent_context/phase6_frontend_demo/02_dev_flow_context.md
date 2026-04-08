# Phase 6 - 開發流程

**階段**: `phase6_frontend_demo`

---

## 📊 開發步驟

```
Phase 1 (INFRA): 前端環境建置
    ↓
Phase 2 (ARCH): Schema 擴展 + API 設計
    ↓ [Checkpoint 1]
    ↓
Phase 3 (CODER): 前端頁面實現
    ↓
Phase 4 (ANALYST): 端到端測試
    ↓ [Checkpoint 2]
    ↓
Phase 5: 交付
```

---

## 🔄 詳細流程

### Phase 1: INFRA - 前端環境建置

**負責**: @INFRA
**任務**:
1. 建立 `frontend/` 目錄結構
2. 初始化 Vue 3 + Vite 專案
3. 安裝依賴：Vue 3, Tailwind CSS, Axios
4. 建立基礎配置檔案

**輸出**:
- `frontend/package.json`
- `frontend/vite.config.js`
- `frontend/tailwind.config.js`

---

### Phase 2: ARCH - Schema 擴展 + API 設計

**負責**: @ARCH
**任務**:
1. 擴展 `request_validator.py` 支援新欄位
2. 更新 API Schema 文件
3. 設計前端表單結構
4. 定義 API 回傳格式

**輸出**:
- `docs/api_schema_v2.md`
- `frontend/src/types/schema.ts`

**⚠️ Checkpoint 1**: 確認 Schema 設計

---

### Phase 3: CODER - 前端頁面實現

**負責**: @CODER
**任務**:
1. 實作表單元件（公司資料、簡介輸入）
2. 實作模式切換（GENERATE / OPTIMIZE）
3. 實作 API 呼叫與結果顯示
4. 實作高風險字眼警示

**輸出**:
- `frontend/src/App.vue`
- `frontend/src/components/BriefForm.vue`
- `frontend/src/components/ResultPanel.vue`
- `frontend/src/components/RiskAlert.vue`
- `frontend/src/api.js`

---

### Phase 4: ANALYST - 端到端測試

**負責**: @ANALYST
**任務**:
1. 測試 GENERATE 模式
2. 測試 OPTIMIZE 模式
3. 測試高風險字眼警示
4. 測試 RWD 響應式設計

**輸出**:
- 測試報告
- Demo 錄影（可選）

**⚠️ Checkpoint 2**: 確認測試結果

---

## ⏱️ 時間估算

| Phase | Agent | 預估時間 |
|-------|-------|---------|
| Phase 1 | INFRA | ~5 分鐘 |
| Phase 2 | ARCH | ~10 分鐘 |
| Phase 3 | CODER | ~20 分鐘 |
| Phase 4 | ANALYST | ~10 分鐘 |
| **總計** | | **~45 分鐘** |
