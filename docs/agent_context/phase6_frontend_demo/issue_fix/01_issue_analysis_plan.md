# 問題分析與修正規劃報告

## 一、問題確認

### 1.1 需求流程分析

根據需求文件 `demand_flow.png` 及相關上下文，真正的流程應該是：

```
求才系統提供：
├── 基本資料
│   ├── 公司名稱 (organ)
│   ├── 統一編號 (organNo)
│   ├── 品牌名稱 (brand_names)
│   ├── 資本額 (capital)
│   ├── 員工人數 (employees)
│   └── ...其他基本資料
│
├── 現有公司簡介 (brief)
│   ├── 有 → OPTIMIZE（優化）
│   └── 無 → GENERATE（生成）→ 系統自動用公司名稱上網搜尋
```

### 1.2 問題確認

**現有實作問題：**

| 檔案 | 問題 |
|------|------|
| `request_validator.py` (L31-36) | GENERATE 模式下要求 `companyUrl` 必填，但需求中**不需要**前端提供 URL |
| `generate_brief.py` (L15,19) | 直接使用 `companyUrl` 進行搜尋，應該改用 `organ` 搜尋 |
| `BriefForm.vue` (L63-65) | 前端驗證 GENERATE 模式需要 `companyUrl` |
| `api.js` (L40-41) | 前端 API 驗證 GENERATE 模式需要 `companyUrl` |

### 1.3 需求驗證

根據需求文件：
- **GENERATE 模式**：系統自動用 `organ`（公司名稱）上網搜尋相關資訊
- **不應該要求前端提供 `companyUrl`**

**結論**：Issue 確認無誤，現有實作與需求不符。

---

## 二、修正工項規劃

### 2.1 修正範圍

#### 2.1.1 後端 API 修改

| 序號 | 檔案 | 修改內容 | 優先權 |
|------|------|----------|--------|
| 1.1 | `src/functions/utils/request_validator.py` | 移除 GENERATE 模式下 `companyUrl` 必填驗證 | P0 |
| 1.2 | `src/functions/utils/generate_brief.py` | 改用 `organ` 進行 web_search，不依賴 `companyUrl` | P0 |
| 1.3 | `src/functions/utils/web_search.py` | 確保無 companyUrl 時使用 organ 搜尋 | P0 |
| 1.4 | `src/functions/utils/response_formatter.py` | 確保不需處理 companyUrl 回傳 | P1 |

#### 2.1.2 前端表單修改

| 序號 | 檔案 | 修改內容 | 優先權 |
|------|------|----------|--------|
| 2.1 | `frontend/src/components/BriefForm.vue` | 移除 companyUrl 欄位（GENERATE 模式下不顯示）| P0 |
| 2.2 | `frontend/src/api.js` | 移除 GENERATE 模式下 companyUrl 驗證 | P0 |
| 2.3 | `frontend/src/components/ResultPanel.vue` | 移除 companyUrl 顯示（若有的話）| P1 |

#### 2.1.3 API Schema 文件修改

| 序號 | 檔案 | 修改內容 | 優先權 |
|------|------|----------|--------|
| 3.1 | `docs/api_schema_v2.md` | 更新 Input Schema，companyUrl 改為選填或移除 | P0 |
| 3.2 | `docs/agent_context/phase6_frontend_demo/01_dev_goal_context.md` | 更新 Input Schema 說明 | P0 |

### 2.2 詳細修改說明

#### 修改 1.1：request_validator.py

**現有程式碼（L31-36）：**
```python
if mode == 'GENERATE':
    company_url = data.get('companyUrl')
    if not company_url or not isinstance(company_url, str):
        raise ValidationError('companyUrl is required for GENERATE mode', details=[
            {'field': 'companyUrl', 'reason': 'required in GENERATE mode'}
        ])
```

**修改為：**
```python
# GENERATE 模式下 companyUrl 不再是必填
# 系統會自動使用 organ 進行網路搜尋
pass  # 移除此驗證區塊
```

#### 修改 1.2：generate_brief.py

**現有程式碼：**
```python
def generate_brief(data):
    company_url = data['companyUrl']
    organ = data['organ']
    url_candidates = web_search(organ, company_url)
    target_url = url_candidates[0] if url_candidates else company_url
```

**修改為：**
```python
def generate_brief(data):
    organ = data['organ']
    # GENERATE 模式：使用 organ 搜尋，不再需要 companyUrl
    url_candidates = web_search(organ, company_url=None)
    if not url_candidates:
        raise ExternalServiceError('無法搜尋到公司相關資訊，請確認公司名稱是否正確')
    target_url = url_candidates[0]
```

#### 修改 1.3：web_search.py

**現有程式碼（L32-33）：**
```python
if company_url:
    return [company_url]
```

**確認**：此邏輯在無 companyUrl 時會正確使用 organ 搜尋，**無需修改**。但需確認當 `company_url=None` 時能正確執行。

#### 修改 2.1：BriefForm.vue

**需要移除/修改的部分：**
1. 移除 `companyUrl` 欄位定義（L20）
2. 移除 mode change 時的 companyUrl 清空邏輯（L47-48）
3. 移除 companyUrl 驗證（L62-66）
4. 移除 companyUrl 提交資料（L99-100）
5. 移除表單中的 companyUrl 輸入欄位（L206-215 區塊）

---

## 三、Development Agent 開發項目清單

### 3.1 需要 development_agent 執行的開發任務

| 任務代號 | 描述 | 負責 Agent | 優先權 |
|----------|------|------------|--------|
| DEV-001 | 修改 request_validator.py，移除 GENERATE 模式下 companyUrl 必填驗證 | development_agent | P0 |
| DEV-002 | 修改 generate_brief.py，改用 organ 進行 web_search | development_agent | P0 |
| DEV-003 | 更新 api_schema_v2.md 文件，companyUrl 改為選填 | development_agent | P0 |
| DEV-004 | 修改 BriefForm.vue，移除 companyUrl 欄位及相關驗證邏輯 | development_agent | P0 |
| DEV-005 | 修改 api.js，移除 GENERATE 模式下 companyUrl 驗證 | development_agent | P0 |
| DEV-006 | 修改 01_dev_goal_context.md，更新 Input Schema 說明 | development_agent | P1 |
| DEV-007 | 執行測試驗證，確認 GENERATE 模式正常運作 | development_agent | P0 |

### 3.2 測試驗證項目

修改完成後需驗證：
1. GENERATE 模式不傳 companyUrl 時能正常運作
2. OPTIMIZE 模式維持正常運作
3. 前端表單在兩種模式下都能正確提交
4. API 回傳結果格式正確

---

## 四、預期影響範圍

### 4.1 功能變更

| 項目 | 變更前 | 變更後 |
|------|--------|--------|
| GENERATE 模式 Input | 需要 companyUrl | 不需要 companyUrl，自動用 organ 搜尋 |
| 前端表單 | GENERATE 模式下需輸入官網 | 無需輸入官網 |
| 網路搜尋 | 使用 companyUrl 或 organ | 僅使用 organ |

### 4.2 向後相容性

此變更為**破壞性變更**：
- 舊版前端若已傳入 companyUrl 仍會正常運作（忽略即可）
- API 文件需更新說明

---

## 五、總結

### 5.1 確認事項

- [x] 確認需求流程：GENERATE 模式應自動用 organ 搜尋
- [x] 確認現有實作問題：要求 companyUrl 必填
- [x] 規劃完整修正工項
- [x] 標註需要 development_agent 開發的項目

### 5.2 下一步行動

請 development_agent 依據本文件執行 DEV-001 至 DEV-007 開發任務。

---

*生成時間：2026-03-31*
*Architect-Agent 分析報告*