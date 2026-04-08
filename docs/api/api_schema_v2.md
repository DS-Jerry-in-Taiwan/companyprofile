# API Schema v2

**更新時間**: 2026-03-31
**說明**: 擴展 Input Schema 支援更多企業資料欄位

---

## 📥 Request Schema

### 基本欄位（維持不變）

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `organNo` | string | ✅ | 機構編號 |
| `organ` | string | ✅ | 機構名稱 |
| `mode` | enum | ✅ | GENERATE / OPTIMIZE |
| `brief` | string | OPTIMIZE 必填 | 現有簡介 |
| `companyUrl` | string | 選填 | 公司網址（GENERATE 模式下可略過，系統將自動以 organ 搜尋） |
| `word_limit` | int | 選填 | 字數限制 (50-2000) |
| `optimization_mode` | enum | 選填 | STANDARD / CONCISE / DETAILED |

### 新增欄位

| 欄位 | 類型 | 必填 | 說明 | 範例 |
|------|------|------|------|------|
| `brand_names` | string[] | 選填 | 品牌名稱 | `["品牌A", "品牌B"]` |
| `tax_id` | string | 選填 | 統一編號 | `"12345678"` |
| `capital` | number | 選填 | 資本額（萬元） | `1000` |
| `employees` | number | 選填 | 員工人數 | `50` |
| `founded_year` | number | 選填 | 成立年份 | `2000` |
| `address` | string | 選填 | 公司地址 | `"台北市信義區..."` |
| `industry` | string | 選填 | 產業類別 | `"資訊服務業"` |
| `industry_desc` | string | 選填 | 產業說明 | `"提供企業..."` |
| `banned_words` | string[] | 選填 | 違法/競品字眼 | `["歧視", "競品"]` |

---

## 📤 Response Schema

| 欄位 | 類型 | 說明 |
|------|------|------|
| `success` | boolean | 是否成功 |
| `organNo` | string | 機構編號 |
| `organ` | string | 機構名稱 |
| `mode` | string | GENERATE / OPTIMIZE |
| `title` | string | 生成標題 |
| `summary` | string | 一句話摘要 |
| `body_html` | string | 公司簡介 HTML |
| `tags` | string[] | 標籤 |
| `risk_alerts` | string[] | 高風險字眼警示 |

---

## 📝 Request 範例

### OPTIMIZE 模式

```json
{
  "organNo": "69188618",
  "organ": "私立揚才文理短期補習班",
  "mode": "OPTIMIZE",
  "brief": "揚才補習班，自民國99年創立以來...",
  "brand_names": ["揚才", "YangCai"],
  "tax_id": "69188618",
  "capital": 500,
  "employees": 20,
  "founded_year": 2010,
  "address": "桃園市龜山區...",
  "industry": "教育服務業",
  "industry_desc": "國高中升學補習班",
  "word_limit": 500,
  "optimization_mode": "STANDARD"
}
```

### GENERATE 模式

```json
{
  "organNo": "12345678",
  "organ": "測試公司",
  "mode": "GENERATE",
  "companyUrl": "https://www.example.com",
  "brand_names": ["TestCo"],
  "tax_id": "12345678",
  "industry": "科技業",
  "word_limit": 300
}
```

---

## 🚨 高風險字眼處理

前端收到 `risk_alerts` 時應顯示：
- 違法文字：紅色警告
- 競品文字：橙色警告

---

## ⚠️ 注意事項

1. 新欄位均為選填，向後相容
2. `banned_words` 由系統提供，前端可讓使用者確認
3. `risk_alerts` 為新增欄位，後端需實作
