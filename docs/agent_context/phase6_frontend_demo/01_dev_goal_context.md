# Phase 6 - 開發目標：前端 Demo 頁

**階段**: `phase6_frontend_demo`
**目的**: 建立公司簡介生成/優化服務的前端 Demo 頁，並擴展 Input Schema 支援更多企業資料欄位。

---

## 🎯 開發目標

### 核心需求

根據 [HackMD 需求文件](https://hackmd.io/tG5w5aDUQyCtxSftxdr7OA) 的描述，前端 Demo 頁需要：

1. **表單輸入**：公司基本資料、公司簡介
2. **模式切換**：GENERATE / OPTIMIZE
3. **即時預覽**：顯示優化/生成結果
4. **高風險字眼警示**：違反就服法/性平法的字眼提示

### 產出物

| 產出物 | 說明 |
|--------|------|
| `frontend/` | 前端專案目錄 |
| `frontend/index.html` | 入口頁面 |
| `frontend/src/` | Vue 3 源碼 |
| `docs/api_schema_v2.md` | 新版 API Schema 文件 |

---

## 📋 Input Schema 新增欄位

### 現有欄位（保持不動）

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `organNo` | string | ✅ | 機構編號 |
| `organ` | string | ✅ | 機構名稱 |
| `mode` | enum | ✅ | GENERATE / OPTIMIZE |
| `brief` | string | OPTIMIZE 必填 | 現有簡介 |
| `companyUrl` | string | GENERATE 必填 | 公司網址 |
| `word_limit` | int | 選填 | 字數限制 (50-2000) |
| `optimization_mode` | enum | 選填 | STANDARD / CONCISE / DETAILED |

### 新增欄位

| 欄位 | 類型 | 必填 | 說明 | 來源 |
|------|------|------|------|------|
| `brand_names` | string[] | 選填 | 品牌名稱（多筆） | oAlias |
| `tax_id` | string | 選填 | 統一編號 | organs |
| `capital` | number | 選填 | 資本額（萬元） | organs |
| `employees` | number | 選填 | 員工人數 | organs |
| `founded_year` | number | 選填 | 成立年份 | organs |
| `address` | string | 選填 | 公司地址 | organs |
| `industry` | string | 選填 | 產業類別 | tCodeTrade |
| `industry_desc` | string | 選填 | 產業說明（200字） | organs |
| `banned_words` | string[] | 選填 | 違法/競品字眼 | 系統提供 |

---

## ✅ 驗收標準

1. 前端表單完整支援新舊欄位
2. GENERATE / OPTIMIZE 兩種模式都能正常運作
3. 高風險字眼有即時警示
4. 結果能正確顯示（Title, Summary, Body）
5. RWD 支援（手機/平板/桌面）

---

## 📁 參考文件

- `docs/agent_config/multi_agent_dev_workflow_v4.0.md`
- `docs/schedule_context/04_agent_prompts_context.md`
- HackMD 需求文件：B.1.1 基本資料
