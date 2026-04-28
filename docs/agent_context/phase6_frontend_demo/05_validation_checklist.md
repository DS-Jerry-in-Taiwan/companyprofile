# Phase 6 - 驗證清單

**階段**: `phase6_frontend_demo`

---

## ✅ 驗證清單

### Phase 1: INFRA 環境建置

- [ ] `frontend/` 目錄已建立
- [ ] `package.json` 存在且格式正確
- [ ] `vite.config.js` 配置正確
- [ ] `npm install` 成功執行
- [ ] `npm run dev` 可啟動開發伺服器

**驗證指令**:
```bash
cd frontend && npm run dev
# 應開啟 http://localhost:5173
```

---

### Phase 2: ARCH Schema 擴展

- [ ] `request_validator.py` 支援新欄位
- [ ] 新欄位驗證邏輯正確（型別、範圍）
- [ ] API 文件更新完成
- [ ] Checkpoint 1 通過

**驗證指令**:
```bash
cd /home/ubuntu/projects/OrganBriefOptimization
python -c "
from src.functions.utils.request_validator import validate_request
data = {
    'organNo': '123',
    'organ': '測試公司',
    'mode': 'OPTIMIZE',
    'brief': 'test',
    'brand_names': ['品牌A'],
    'capital': 1000
}
result = validate_request(data)
print('OK:', result)
"
```

---

### Phase 3: CODER 前端實現

- [ ] `BriefForm.vue` 可顯示所有欄位
- [ ] 模式切換正常（GENERATE / OPTIMIZE）
- [ ] 表單驗證正常（必填欄位）
- [ ] `ResultPanel.vue` 可顯示結果
- [ ] `RiskAlert.vue` 可顯示警示
- [ ] API 呼叫成功
- [ ] 錯誤處理正常

**驗證指令**:
```bash
# 啟動後端
cd /home/ubuntu/projects/OrganBriefOptimization
python run_api.py &

# 啟動前端
cd frontend && npm run dev

# 測試 API
curl -X POST http://127.0.0.1:5000/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo": "123", "organ": "測試", "mode": "OPTIMIZE", "brief": "test"}'
```

---

### Phase 4: ANALYST 測試驗證

- [x] GENERATE 模式測試通過
- [x] OPTIMIZE 模式測試通過
- [x] 高風險字眼警示測試通過
- [x] RWD 桌面版測試通過
- [x] RWD 平板版測試通過
- [x] RWD 手機版測試通過
- [x] Checkpoint 2 通過

---

## 📊 驗證結果記錄

| Phase | 驗證項目 | 狀態 | 備註 |
|-------|---------|------|------|
| INFRA | 環境建置 | ✅ | |
| ARCH | Schema 擴展 | ✅ | 已支援新欄位 |
| ARCH | Checkpoint 1 | ✅ | |
| CODER | 前端實現 | ✅ | |
| ANALYST | OPTIMIZE 模式 | ✅ | 已測試通過 |
| ANALYST | GENERATE 模式 | ✅ | 已修正流程，無需 companyUrl |
| ANALYST | 高風險字眼警示 | ✅ | risk_alerts 正常回傳 |
| ANALYST | RWD | ✅ | 桌面/平板/手機 grid-cols-1 lg:grid-cols-2 配置正確 |
| ANALYST | Checkpoint 2 | ✅ | 前端/API/響應式均正常 |

---

## 📝 開發記錄

### 2026/03/31 - GENERATE 流程修正
- 問題：原本要求輸入 companyUrl，與需求不符
- 修正：移除 companyUrl 必填，改由系統自動用 organ 搜尋
- 修改檔案：
  - `request_validator.py`
  - `generate_brief.py`
  - `BriefForm.vue`
  - `api.js`
  - `docs/api_schema_v2.md`
