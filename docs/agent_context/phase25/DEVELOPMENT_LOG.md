# Phase 25 開發紀錄

## 版本
- **文件版本**: v0.3.0
- **建立日期**: 2026-04-27
- **目標版本**: v0.4.0

---

## 概述

### 目標
- 搜尋前清理：Prompt 要求 LLM 輸出不要帶千位逗號
- 後處理清理：post_processing 加上數字格式清理與簡化
- 錯誤處理強化：補齊 catch-all、統一 ErrorCode
- DB schema 優化：id PK、request_id 移除、trace_id 統一

### 背景
- 問題：搜尋結果中的數字帶有千位逗號（如 `2,582,526,570`）
- 直接輸出會造成「實收資本額高達新台幣 2，582，526，570 元」
- 期望輸出：「資本額新臺幣 2億元」
- GitHub: `https://github.com/DS-Jerry-in-Taiwan/companyprofile.git`

---

## 開發日誌

### 📅 2026-04-27

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| - | Phase 25 規劃 | ✅ | 建立開發計劃 |
| - | **Step 1**: Prompt 加入數字格式要求 | ✅ | prompt_builder.py |
| - | **Step 2**: 後處理加入數字清理 clean_number_format() | ✅ | post_processing.py |
| - | **Step 3**: 測試驗證 | ✅ | 15/15 測試通過 |
| - | **Step 4**: 新增數字簡化規則 simplify_number() | ✅ | 34/34 測試通過 |
| - | **Step 5**: 1111 實際案例測試 | ✅ | 19/19 |
| - | **Step 6**: API mock 整合測試 | ✅ | 34/34 |
| - | **Step 7**: 真實 API 測試 (port 5000) | ✅ | 21/21, 修正 optimization_mode null |
| - | **Step 8**: 三種模式實測 (STANDARD/CONCISE/DETAILED) | ✅ | DB 驗證通過 |
| - | **Step 9**: DB schema 改造 (id PK, 移除 request_id) | ✅ | 含 codebase 全部更新 |
| - | **Step 10**: trace_id 統一 (trace- → t-) | ✅ | 三處 llm_service + structured_logger |
| - | **Step 11**: Error handling 補強 | ✅ | catch-all + ErrorCode API_009 統一 |
| - | **Step 12**: Git commit & push | ✅ | 6 commits, pushed to origin |
| - | **Step 13**: README 更新至 v0.4.0 | ✅ | 完整 Phase 25 章節 |

---

## Step 追蹤

### Step 1-6: Phase 25 核心功能
- [x] `prompt_builder.py` 加入數字格式規範
- [x] `post_processing.py` `clean_number_format()` + `simplify_number()`
- [x] 測試: 34 + 19 + 34 = 87 ✅

### Step 7: 真實 API 測試 (port 5000)
- [x] Flask test client 模擬 API 請求
- [x] 發現 `optimization_mode` response 為 null
- [x] 修正 `response_formatter.py` 補上欄位
- [x] DB 驗證 3 筆記錄正確

### Step 8: 三種模式實測
- [x] STANDARD / CONCISE / DETAILED 全部通過
- [x] DB 含所有 8 個 user_input keys
- [x] 測試期間遇到 Gemini 429 rate limit

### Step 9: DB schema 改造
- [x] `sqlite_adapter.py`: `id` auto-increment PK
- [x] 移除 `request_id`（由 `trace_id` 取代）
- [x] 補 `optimization_mode`、`user_input`、`organ_name` 等欄位
- [x] `base.py`: 新增 `save_error()` / `list_errors()` 抽象方法

### Step 10: trace_id 統一
- [x] `structured_logger.py`: `trace-` → `t-`
- [x] `functions/utils/llm_service.py`: 統一格式
- [x] `services/llm_service.py`: 統一格式

### Step 11: Error handling 補強
- [x] `generate_brief.py`: 新增 `except Exception` catch-all
- [x] `api_controller.py`: 泛用 except 改用 `ErrorCode.API_009`
- [x] 新增 `error_logger.py` ErrorLogger 模組

### Step 12: Git
- [x] 6 commits 依功能拆分
- [x] 已 push 到 `origin-private/dev-jerry`

### Step 13: README
- [x] 版本 v0.3.9 → v0.4.0
- [x] 完整 Phase 25 變更記錄

---

## 設計共識

### 問題案例

```
修改前:    新台幣 2,582,526,570 元
清理後:    新台幣 2582526570 元     (clean_number_format 移除逗號)
簡化後:    新台幣 25.8億元          (simplify_number 轉為自然單位)
```

### Pipeline 順序

```
LLM 輸出 (含千位逗號/無逗號)
  ↓
clean_number_format()    移除全形/半形千位逗號
  ↓
simplify_number()        將大數字轉為億/萬單位 (只處理後綴「元」)
```

### 錯誤處理流程 (三層)

```
api_controller.py
  ├─ except ValidationError                        → 400 + ve.code
  ├─ except (ExternalServiceError, LLMServiceError) → 500 + se.code
  └─ except Exception                              → 500 + API_009
        ↑
generate_brief.py
  ├─ except ExternalServiceError → LLMServiceError
  └─ except Exception           → LLMServiceError (保留原始 code)
        ↑
LangGraph invoke()
  └─ error_handled → ExternalServiceError(code, message)
```

### DB Schema (最終版)

```sql
-- llm_responses
id                INTEGER PRIMARY KEY AUTOINCREMENT
trace_id          VARCHAR INDEX
status            VARCHAR DEFAULT 'success'
error_code        VARCHAR
organ_no          VARCHAR INDEX
organ_name        VARCHAR
company_url       VARCHAR
mode              VARCHAR
optimization_mode VARCHAR
user_input        TEXT
prompt_raw        TEXT
prompt_structure_key VARCHAR
prompt_opening_key   VARCHAR
prompt_sentence_key  VARCHAR
prompt_template_name VARCHAR
response_raw      TEXT
is_json           INTEGER DEFAULT 0
word_count        INTEGER
tokens_used       INTEGER
model             VARCHAR
latency_ms        INTEGER
created_at        VARCHAR INDEX
duration_ms       INTEGER
```

---

## 驗收標準

| 標準 | 說明 |
|------|------|
| 數字千位逗號移除 (半形) | `2,582,526,570` → `2582526570` |
| 數字千位逗號移除 (全形) | `2，582，526，570` → `2582526570` |
| 數字簡化 (≥1億) | `2582526570元` → `25.8億元` |
| 數字簡化 (≥1萬) | `8000000元` → `800萬元` |
| 不誤轉年份 | `1987`（<10000）→ 不處理 |
| 不誤轉統一編號 | `12345678`（無後綴元）→ 不處理 |
| 不誤轉日期 | `19620825`（無後綴元）→ 不處理 |
| API response optimization_mode | 不為 null |
| DB optimization_mode | 正確儲存 standard/concise/detailed |
| DB id | auto-increment PK |
| trace_id 格式 | 統一 `t-{hex}` |
| Error code | 全部來自 ErrorCode 枚舉，無 hardcode 字串 |

---

## Git Commits

| # | Hash | 說明 |
|:-:|------|------|
| 1 | `72c6ab7` | feat: Phase 25 數字格式清理與簡化 |
| 2 | `67fbaa7` | fix: 錯誤處理補強 — catch-all + ErrorCode 統一 |
| 3 | `8a57f85` | refactor: DB schema 更新 + trace_id 統一 |
| 4 | `0a61bd6` | fix: Response 補 optimization_mode |
| 5 | `e9df011` | chore: 清理 word_limit 遺留程式碼 + README |
| 6 | `10e1b91` | docs: README 更新至 v0.4.0 |

---

## 版本變更

| 版本 | 日期 | 變更 |
|------|------|------|
| **v0.4.0** | **2026-04-27** | **Phase 25 完成** — 數字格式清理、錯誤處理補強、DB schema 優化 |
| v0.3.9 | 2026-04-27 | Phase 24 完成 |
