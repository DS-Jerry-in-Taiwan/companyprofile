# 可選數值欄位提交問題分析報告

## 分析日期
2024-04-10

---

## 一、問題描述

用戶回報：當填寫可選欄位（如 capital, employees）後，無法送出 POST 請求生成公司簡介。

---

## 二、程式碼流程分析

### 2.1 前端流程（正確）

```
BriefForm.vue
  │
  ├─► validateForm() - 驗證必填欄位 + word_limit
  │   ✅ 沒有驗證 capital/employees/founded_year
  │
  ├─► handleSubmit() - 組裝提交資料
  │   ├─► parseInt("100") → 100 ✅
  │   ├─► parseInt("abc") → NaN ⚠️
  │   └─► parseInt("-10") → -10 ⚠️
  │
  └─► emit('submit', submitData) - 發送請求
```

### 2.2 後端流程（正確）

```
api_controller.py
  │
  ├─► validate_request() - 驗證必填欄位 + word_limit
  │   ✅ 沒有驗證 capital/employees/founded_year
  │
  ├─► dispatch_core_logic() - 分派邏輯
  │
  └─► generate_brief() - 生成簡介
      ⚠️ 沒有使用 capital/employees 等欄位
```

---

## 三、測試驗證結果

| 測試案例 | 前端處理 | 後端驗證 | 結果 |
|----------|----------|----------|------|
| capital = "" | 不提交 | 通過 | ✅ 正常 |
| capital = "100" | parseInt → 100 | 通過 | ✅ 正常 |
| capital = "abc" | parseInt → NaN ⚠️ | 通過 | ⚠️ 可能問題 |
| capital = "-10" | parseInt → -10 | 通過 | ⚠️ 可能問題 |
| employees = "abc" | parseInt → NaN ⚠️ | 通過 | ⚠️ 可能問題 |
| employees = "-5" | parseInt → -5 | 通過 | ⚠️ 可能問題 |

---

## 四、根因分析

### 4.1 最可能的原因

| 可能性 | 原因 | 說明 |
|--------|------|------|
| 🔴 高 | 後端伺服器未運行 | 最常見原因 |
| 🔴 中 | API 請求失敗 | 網路或 CORS 問題 |
| 🟡 低 | NaN 傳遞導致問題 | parseInt 失敗 |

### 4.2 不是問題的原因

- ✅ 後端 validate_request() 不會阻止這些欄位
- ✅ 前端 handleSubmit() 正確處理了大多數情況
- ✅ API 路由配置正確（/api → /）

---

## 五、請確認以下資訊

為了進一步診斷問題，請提供：

1. **錯誤訊息**：瀏覽器控制台顯示什麼錯誤？
2. **網路狀態**：瀏覽器 Network 標籤中，請求的狀態碼是什麼？
3. **後端狀態**：後端 Flask 伺服器是否正在運行？

---

## 六、臨時解決方案

如果需要立即解決，可以：

### 6.1 前端加強驗證（推薦）

在 `validateForm()` 中添加：

```javascript
// 數值欄位驗證
if (form.value.capital?.trim()) {
  const val = parseInt(form.value.capital)
  if (isNaN(val) || val <= 0) {
    errors.value.push('資本額必須為正數')
  }
}

if (form.value.employees?.trim()) {
  const val = parseInt(form.value.employees)
  if (isNaN(val) || val <= 0) {
    errors.value.push('員工人數必須為正數')
  }
}

if (form.value.founded_year?.trim()) {
  const val = parseInt(form.value.founded_year)
  if (isNaN(val) || val < 1900 || val > 2100) {
    errors.value.push('成立年份必須在 1900-2100 之間')
  }
}
```

### 6.2 後端添加驗證

在 `request_validator.py` 中添加驗證邏輯。

---

## 七、結論

目前的程式碼邏輯是正確的，問題可能是：

1. **後端伺服器未運行**（最可能）
2. **網路連接問題**
3. **其他運行時錯誤**

請提供具體的錯誤訊息，以便進一步診斷。

---

**分析人**：Project Analyst  
**版本**：v1.0