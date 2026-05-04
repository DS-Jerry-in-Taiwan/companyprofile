# Phase 28 開發日誌

## 版本

- **開始日期**: 2026-04-30
- **目標版本**: v0.6.0

---

## Phase A: src/storage/__init__.py 全域入口

### 📅 2026-04-30

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| 10:00 | 建立 `src/storage/__init__.py` 提供 `init_storage(config)` / `get_storage()` / `is_initialized()` | ✅ | 強制傳入 config，不自己讀檔 |
| 10:10 | 新增 `tests/test_storage_init.py` | ✅ | 5 項測試 |
| 10:15 | 修復 `test_sqlite_adapter.py` 與 `test_storage_integration.py` 中 `request_id` → `trace_id` | ✅ | `request_id` 欄位已不存在於 model 中 |
| 10:20 | 全部 22 項 storage 測試 PASS | ✅ | 無 regression |

### 驗證結果

```
寫入檔案型 SQLite:  ✅ save_response → True
讀回資料:           ✅ get_response → trace_id=正確
直接讀取 .db 檔案:   ✅ sqlite3 SELECT 確認資料存在磁碟
錯誤日誌寫入查詢:   ✅ save_error + list_errors(error_code=)
list_by_organ:     ✅ 依 organ_no 回傳正確資料
```

---

## Phase B: DynamoDB Adapter + Factory 擴充

### 📅 2026-04-30

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| 10:30 | 新增 `src/storage/dynamodb_adapter.py` | ✅ | 實作 `StorageInterface`，使用 boto3 |
| 10:40 | 修改 `src/storage/factory.py` 新增 `type=dynamodb` | ✅ | 新增 import 分支 |
| 10:45 | 更新 `config/storage_config.json` 加入 DynamoDB profiles | ✅ | lambda-dev / lambda-prod |
| 11:00 | 新增 `tests/test_dynamodb_adapter.py` | ✅ | 14 項測試，全部 PASS |
| 11:05 | 修復 `datetime.utcnow()` deprecation warning | ✅ | 改為 `datetime.now(timezone.utc)` |

### 驗證結果

```
Factory 建立 DynamoDBStorage: ✅
5 個方法簽章與 Interface 一致: ✅
save→get mock 流程正確:       ✅
list_by_organ GSI 查詢正確:   ✅
SQLite 不受影響:              ✅
```

---

## Phase C: Consumer 重構

### 📅 2026-04-30

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| 11:15 | 修改 `api_controller.py` — 加入環境判斷 + `init_storage()` | ✅ | STAGE=dev/prod → DynamoDB，其他 → SQLite |
| 11:15 | 移除 `_save_failed_request_to_llm_responses()` 函數 + 3 處呼叫 | ✅ | 功能已被 ErrorLogger + call_llm 涵蓋 |
| 11:20 | 修改 `error_logger.py` — `_init_storage()` 改 call `get_storage()` | ✅ | 移除自己讀 config 邏輯 |
| 11:25 | 修改 `utils/llm_service.py` — `_get_storage()` 改 call `get_storage()` | ✅ | 移除模組層級 `_storage_instance` |
| 11:30 | 修改 `services/llm_service.py` — `_get_storage()` 改 call `get_storage()` | ✅ | 移除 `StorageFactory` import |
| 11:35 | 36 項 storage 測試全部 PASS | ✅ | 無 regression |
| 11:40 | 驗證 ErrorLogger 共用同一個 instance | ✅ | `全部相同: True` |

### 環境切換驗證

```
無 STAGE → SQLite (development):   ✅
STAGE=dev → DynamoDB (dev-llm-responses): ✅
```

---

## Phase D: serverless.yml DynamoDB + IAM

### 📅 2026-04-30

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| 11:45 | 新增 `LlmResponsesTable` (PK: trace_id, SK: created_at, GSI: organ_no, status) | ✅ | PAY_PER_REQUEST |
| 11:45 | 新增 `ErrorLogsTable` (PK: trace_id, SK: created_at, GSI: error_code) | ✅ | PAY_PER_REQUEST |
| 11:45 | 新增 DynamoDB IAM: PutItem, GetItem, Query, Scan | ✅ | 限兩張 Table + GSI |
| 12:00 | `sls deploy --stage dev` 成功 | ✅ | 156s |
| 12:05 | DynamoDB tables 建立確認 | ✅ | dev-llm-responses, dev-error-logs |

---

## Phase E: 移除 sqlalchemy 依賴

### 📅 2026-04-30

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| 12:10 | 確認 `sqlalchemy` 不在任何 requirements.txt 中 | ✅ | Lambda Docker build 本來就沒裝 |

---

## 部署驗證

### 📅 2026-04-30

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| 13:00 | 部署至 dev 環境 | ✅ | `sls deploy --stage dev -p office-mfa` |
| 13:05 | DynamoDB Table 確認 | ✅ | `dev-llm-responses`, `dev-error-logs` 已存在 |
| 13:10 | API 測試 (validation error) | ✅ | 400 + error log 寫入 DynamoDB |
| 13:15 | API 測試 (success) | ✅ | 200 + response 寫入 DynamoDB |
| 13:20 | CloudWatch 確認 Storage 訊息 | ✅ | `Storage initialized: type=dynamodb` |
| 13:20 | CloudWatch 確認寫入成功 | ✅ | `DYNAMODB WRITE | table=dev-llm-responses` |
| 13:25 | CloudWatch 確認無 Storage 錯誤 | ✅ | 無 `Storage not available` 訊息 |

### CloudWatch Logs 對比

```
部署前:
  [WARNING] [Storage] 儲存初始化失敗: No module named 'sqlalchemy'
  [WARNING] [Storage] 儲存未初始化，跳過寫入
  [WARNING] Storage not available, cannot save error log

部署後:
  [INFO]  Storage initialized: type=dynamodb
  [INFO]  Storage initialized: DynamoDB (dev-llm-responses)
  [INFO]  DYNAMODB WRITE | table=dev-llm-responses trace_id=...
  [INFO]  [Storage] 寫入成功 trace_id=...
```

### 成功寫入 DynamoDB 資料

```
Table: dev-llm-responses
trace_id:      t-705778ea1e044c92
organ_no:      11111111
organ_name:    測試公司
mode:          GENERATE
optimization:  standard
model:         gemini-3-flash-preview
tokens_used:   3926
latency_ms:    13131
word_count:    207
```

---

## 檔案異動總覽

| 動作 | 檔案 |
|------|------|
| 新增 | `src/storage/__init__.py` |
| 新增 | `src/storage/dynamodb_adapter.py` |
| 新增 | `tests/test_storage_init.py` |
| 新增 | `tests/test_dynamodb_adapter.py` |
| 修改 | `src/storage/factory.py` |
| 修改 | `src/functions/api_controller.py` |
| 修改 | `src/functions/utils/error_logger.py` |
| 修改 | `src/functions/utils/llm_service.py` |
| 修改 | `src/services/llm_service.py` |
| 修改 | `config/storage_config.json` |
| 修改 | `serverless.yml` |
| 修改(修bug) | `tests/test_sqlite_adapter.py` |
| 修改(修bug) | `tests/test_storage_integration.py` |

## 測試結果

```
36 passed in 0.87s
```

---

## Phase 28 結論

Phase 28 完成儲存層中央集權 + 雙軌儲存，地端 SQLite、雲端 DynamoDB 依環境自動切換。

### 環境切換邏輯

```
本機開發（無 STAGE）→ SQLite（data/llm_responses.db）
Lambda dev（STAGE=dev）→ DynamoDB（dev-llm-responses）
Lambda prod（STAGE=prod）→ DynamoDB（prod-llm-responses）
```

### Lambda 上不再出現的錯誤

~~`[Storage] 儲存初始化失敗: No module named 'sqlalchemy'`~~
~~`Storage not available, cannot save error log`~~
