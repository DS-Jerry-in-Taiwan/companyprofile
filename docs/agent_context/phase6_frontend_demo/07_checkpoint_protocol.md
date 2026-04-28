# Phase 6 - Checkpoint 協議

**階段**: `phase6_frontend_demo`

---

## 🛑 Checkpoint 定義

### Checkpoint 1: Schema 設計確認

**觸發時機**: @ARCH 完成 Schema 擴展設計後

**確認項目**:
- [ ] 新欄位定義完整（brand_names, tax_id, capital 等）
- [ ] 驗證邏輯正確（必填、型別、範圍）
- [ ] 前端表單結構合理
- [ ] API 文件更新完整

**決策選項**:
- ✅ 確認通過 → @CODER 開始前端實現
- 🔍 詳細檢查 → 顯示完整 Schema
- ❌ 問題：[描述] → @ARCH 修正

---

### Checkpoint 2: 測試結果確認

**觸發時機**: @ANALYST 完成測試後

**確認項目**:
- [ ] GENERATE 模式測試通過
- [ ] OPTIMIZE 模式測試通過
- [ ] 高風險字眼警示正常
- [ ] RWD 三種裝置測試通過
- [ ] API 整合正常

**決策選項**:
- ✅ 確認通過 → Phase 6 完成
- 🔍 詳細檢查 → 顯示測試報告
- ❌ 問題：[描述] → @CODER 修正

---

## 🔄 重新執行規則

| 情境 | 處理方式 |
|------|---------|
| Schema 設計不合理 | 重新執行 Phase 2 (ARCH) |
| 前端功能有 Bug | 重新執行 Phase 3 (CODER) |
| 測試未通過 | 重新執行 Phase 4 (ANALYST) |

---

## 📊 Checkpoint 決策記錄

| Checkpoint | 狀態 | 決策 | 備註 |
|-----------|------|------|------|
| Checkpoint 1 | ⬜ | - | |
| Checkpoint 2 | ⬜ | - | |
