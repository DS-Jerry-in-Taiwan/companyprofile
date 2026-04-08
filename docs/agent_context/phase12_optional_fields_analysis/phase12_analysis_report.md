# Phase12 可選數值欄位問題分析報告

## 分析日期
2024-04-10

---

## 一、前端可選欄位清單

根據 `BriefForm.vue`，所有可選欄位如下：

| 欄位名稱 | 類型 | 前端處理方式 | 潛在問題 |
|----------|------|--------------|----------|
| brand_names | string[] | split(',').map().filter() | 空字串、格式錯誤 |
| tax_id | string | trim() | 無 |
| capital | number | parseInt() | 非數字輸入 → NaN |
| employees | number | parseInt() | 非數字輸入 → NaN |
| founded_year | number | parseInt() | 非數字輸入 → NaN |
| address | string | trim() | 無 |
| industry | string | trim() | 無 |
| industry_desc | string | trim() | 無 |

---

## 二、問題欄位分析

### 2.1 高風險欄位（數值類型）

| 欄位 | 問題描述 | 錯誤情境 | 影響 |
|------|----------|----------|------|
| **capital** | parseInt 失敗 | 輸入 "abc" → NaN | 提交失敗或後端處理錯誤 |
| **employees** | parseInt 失敗 | 輸入 "abc" → NaN | 提交失敗或後端處理錯誤 |
| **founded_year** | parseInt 失敗 | 輸入 "abc" → NaN | 提交失敗或後端處理錯誤 |

**測試驗證**：
```javascript
parseInt("abc")    // → NaN
parseInt("")       // → NaN  
parseInt("   ")    // → NaN
parseInt("100.5")  // → 100 (可行)
parseInt("-10")    // → -10 (負數未驗證)
```

### 2.2 中風險欄位（陣列類型）

| 欄位 | 問題描述 | 錯誤情境 | 影響 |
|------|----------|----------|------|
| **brand_names** | split 處理不當 | 輸入 ", , " → 空陣列 | 可能導致格式錯誤 |

**測試驗證**：
```javascript
"a,b,c".split(',').map(s => s.trim()).filter(s => s)
// → ['a', 'b', 'c'] ✓

",,".split(',').map(s => s.trim()).filter(s => s)
// → [] (空陣列，可能非預期)
```

### 2.3 低風險欄位（字串類型）

| 欄位 | 處理方式 | 安全性 |
|------|----------|--------|
| tax_id | trim() | ✅ 安全 |
| address | trim() | ✅ 安全 |
| industry | trim() | ✅ 安全 |
| industry_desc | trim() | ✅ 安全 |

---

## 三、具體問題情境

### 情境 1：用戶輸入非數字
```
capital: "abc"
employees: "test"
founded_year: "xyz"
```

**前端處理**：
```javascript
submitData.capital = parseInt("abc")   // NaN
submitData.employees = parseInt("test") // NaN
submitData.founded_year = parseInt("xyz") // NaN
```

**潛在後果**：
- NaN 傳遞給後端，可能導致：
  - 後端類型錯誤
  - 資料庫寫入失敗
  - JSON 序列化問題

### 情境 2：用戶輸入負數
```
capital: "-100"
employees: "-5"
founded_year: "-2000"
```

**前端處理**：
```javascript
parseInt("-100")  // -100 (沒有驗證負數)
```

**潛在後果**：
- 負數資本額/員工人數不合理
- 後端未驗證可能導致資料異常

### 情境 3：用戶輸入浮點數
```
capital: "100.5"
employees: "10.9"
```

**前端處理**：
```javascript
parseInt("100.5")  // 100 (自動取整)
```

**潛在後果**：
- 可能造成資料不一致（用戶預期 100.5，實際存 100）

---

## 四、後端現況分析

### 4.1 當前後端驗證

檢視 `request_validator.py`：
- ✅ word_limit 驗證（50-2000）
- ✅ optimization_mode 驗證
- ❌ **無 capital/employees/founded_year 驗證**
- ❌ **無 brand_names/tax_id 驗證**

### 4.2 後端缺失的驗證

```python
# 缺少以下驗證：
- capital: 應該是正整數
- employees: 應該是正整數
- founded_year: 應該是合理年份 (1900-2099)
- brand_names: 應該是陣列
- tax_id: 應該是字串
```

---

## 五、結論與建議

### 問題範圍

**並非所有可選欄位都有問題**，只有以下欄位需要關注：

| 風險等級 | 欄位 | 問題 |
|----------|------|------|
| 🔴 高 | capital, employees, founded_year | parseInt 可能產生 NaN或負數 |
| 🟡 中 | brand_names | split 可能產生空陣列 |
| 🟢 低 | tax_id, address, industry, industry_desc | 無問題 |

### 建議解決方案

1. **前端加強驗證**
   - 數值欄位：檢查 isNaN() 後再提交
   - 負數欄位：驗證 > 0
   - 年份欄位：驗證合理範圍

2. **後端加強驗證**
   - 新增可選欄位的驗證邏輯
   - 類型檢查 + 範圍檢查
   - 錯誤訊息回饋

---

**分析人**：Project Analyst  
**版本**：v1.0