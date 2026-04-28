# Phase 24 開發紀錄

## 版本
- **文件版本**: v0.3.0
- **建立日期**: 2026-04-24
- **目標版本**: v0.4.1
- **最終版本**: v0.4.1

---

## 概述

### 目標
- 建立 LLM 回應存儲層
- 抽象化存儲接口，支持多元存儲方案
- 開發環境用 SQLite，生產環境預留雲端接口
- **錯誤日誌記錄功能**（Phase 24b）

### 背景
- Phase 23 延伸需求：LLM 回應未完整存儲
- 僅存於日誌，最多 500 字符
- 需要完整存儲支持：調試排查、數據分析、合規審計
- **Phase 24b 背景**：optimization_mode 參數傳遞錯誤 + 需要錯誤日誌

---

## 開發日誌

### 📅 2026-04-24

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| - | 建立 Phase 24 目錄 | ✅ | 從 Phase 23 延伸 |
| - | 討論存儲架構 | ✅ | 抽象層 + 適配器 |
| - | 討論 SQLite vs SQLAlchemy | ✅ | 確認 SQLAlchemy 更成熟 |
| - | 討論工廠模式 vs 註冊模式 | ✅ | 確認用工廠模式 |
| - | 討論 schema 放置位置 | ✅ | schema 在 adapter 內 |
| - | 結案 Phase 23 | ✅ | Phase 24 獨立 |
| - | 建立 Phase 24 文件 | ✅ | 初始化 |
| - | **Step 1**: 建立目錄結構 | ✅ | 4 個文件已建立，可導入 |
| - | **Step 2**: 建立抽象層 | ✅ | StorageInterface 3 個抽象方法已定義 |
| - | **Step 3**: 單元測試抽象層 | ✅ | 5 個測試用例全部通過 |
| - | **Step 4**: SQLite 適配器實作 | ✅ | SQLAlchemy schema + 3 個方法已實現 |
| - | **Step 5**: 單元測試 SQLite 適配器 | ✅ | 5 個測試用例全部通過 |
| - | **Step 6**: 工廠層實作 | ✅ | StorageFactory.create() 实现 |
| - | **Step 7**: 單元測試工廠 | ✅ | 4 個測試用例全部通過 |
| - | **Step 8**: 配置層實作 | ✅ | config/storage_config.json 已建立 |
| - | **Step 9**: 集成測試 | ✅ | 3 個測試用例全部通過 |
| - | **Step 10**: LLM 服務集成 | ✅ | llm_service.py 已整合存儲（非同步寫入） |
| - | **後續優化**: 同步→非同步 | ✅ | threading.Thread 背景寫入，不阻塞主流程 |
| - | **Step 11**: 最終驗收 | ✅ | 17 個測試全部通過 |
| - | **Step 12**: Schema 擴展（+4 framework metadata 欄位） | ✅ | Phase 23 整合 |
| - | **Step 13**: build_generate_prompt() 回填 _metadata | ✅ | 向後相容 |
| - | **Step 14**: llm_service.py 串接 4 個 framework keys | ✅ | 寫入新欄位 |
| - | **Step 15**: company_brief_graph.py wiring | ✅ | _prompt_meta → call_llm() |
| - | **Step 16**: duration_ms 修補 | ✅ | _duration_ms 全流程計時 |
| - | **Step 17**: .gitignore 更新 | ✅ | data/llm_responses.db |

---

## 設計共識

### 架構三層

```
┌─────────────────────────────────────────────┐
│          調用層 (LLM Service)               │
│           llm_service.py                   │
│           調用 storage.save_response()     │
└─────────────────┬─────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│          工廠層 (StorageFactory)            │
│      storage/factory.py                   │
│      根據配置創建適配器                  │
└─────────────────┬─────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  ┌─────────────────────────────────────┐  │
│  │        抽象層 (StorageInterface)    │  │
│  │   定義接口：save/get/list_by_organ   │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │        適配器層                     │  │
│  │  SQLiteStorage (SQLAlchemy)         │  │
│  │  PostgreSQLStorage (SQLAlchemy)   │  │
│  │  DynamoDBStorage (boto3)          │  │
│  │  S3Storage (boto3)               │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 設計共識

| 共識 | 說明 |
|------|------|
| 模式 | 工廠模式 |
| schema 位置 | 在各自 adapter.py 內 |
| 連接配置 | config 統一管理 |
| 抽象層 | StorageInterface (不變) |
| 實現層 | SQLAlchemy / boto3 |

### 技術选型

| 存儲類型 | 工具 |
|----------|------|
| SQLite | SQLAlchemy |
| PostgreSQL | SQLAlchemy |
| DynamoDB | boto3 |
| S3 | boto3 |

---

## 步骤追踪

### Step 1: 建立目录结构
- [x] 建立 `src/storage/` 目录
- [x] 创建 `__init__.py`, `base.py`, `factory.py`, `sqlite_adapter.py`
- [x] 测试通过 ✅

### Step 2: 建立抽象层
- [x] 定义 `StorageInterface`
- [x] 3 个抽象方法：save_response, get_response, list_by_organ
- [x] 测试通过 ✅

### Step 3: 单元测试抽象层
- [x] 5 个测试用例 (UT-03-01 ~ UT-03-05)
- [x] 全部通过 ✅
- [x] `tests/test_storage_base.py` 已创建

### Step 4: SQLite 适配方实作
- [x] SQLAlchemy schema 定义（18 字段，含 4 個 Phase 23 framework metadata）
- [x] 实现 save_response / get_response / list_by_organ
- [x] 使用 SQLAlchemy 2.0 style（session.get, select）
- [x] 测试通过 ✅

### Step 5: 单元测试 SQLite
- [x] 5 个测试用例 (UT-05-01 ~ UT-05-05)
- [x] 全部通过 ✅
- [x] `tests/test_sqlite_adapter.py` 已创建

### Step 6: 工廠层实作
- [x] StorageFactory.create() 静态方法
- [x] 根据 config.type 创建适配器
- [x] 未知 type 抛出 ValueError
- [x] 测试通过 ✅

### Step 7: 单元测试工廠
- [x] 4 个测试用例 (UT-07-01 ~ UT-07-04)
- [x] 全部通过 ✅
- [x] `tests/test_storage_factory.py` 已创建

### Step 8: 配置层实作
- [x] `config/storage_config.json` 已建立
- [x] 支持 development 环境配置
- [x] JSON 格式验证通过 ✅

### Step 9: 集成测试
- [x] 3 个集成测试 (IT-09-01 ~ IT-09-03)
- [x] 全部通过 ✅
- [x] `tests/test_storage_integration.py` 已创建

### Step 10: LLM 服务集成
- [x] llm_service.py 导入 StorageFactory
- [x] 惰性初始化存储适配器（首次使用时加载）
- [x] generate() 和 optimize() 调用后保存响应
- [x] 存储失败不影响主流程（try-catch 静默处理）
- [x] 导入测试通过 ✅

### Step 11: 最终验收
- [x] 单元测试 14 个 + 集成测试 3 个 = 17 个全部通过
- [x] 版本 v0.4.0
- [x] Phase 24 完成 ✅

### Step 12: Schema 扩展（Phase 23 framework metadata）
- [x] 新增 4 欄位：prompt_structure_key / opening_key / sentence_key / template_name
- [x] LLMResponse schema 擴展至 18 欄位
- [x] 版本 v0.4.1 ✅

### Step 13: build_generate_prompt() 回填 _metadata
- [x] 新增 _metadata 選用字典參數
- [x] 回填 template_name / structure_key / opening_key / sentence_key
- [x] 向後相容：不傳 _metadata 時行為不變
- [x] 驗證通過 ✅

### Step 14: llm_service.py 串接 framework keys
- [x] call_llm() → _call_llm_with_retry() → _call_llm_original() → _call_llm_core()
  全部新增 4 個 framework key 參數
- [x] _call_llm_core() 在 _try_save_response() 時寫入這 4 個欄位
- [x] duration_ms 修補：_duration_ms（含 parsing 處理的完整時間）
- [x] 驗證通過 ✅

### Step 15: company_brief_graph.py wiring
- [x] generate_node() 建立 _prompt_meta={} 字典
- [x] 傳入 build_generate_prompt(_metadata=_prompt_meta)
- [x] 提取 framework keys，傳遞至 call_llm()
- [x] 驗證通過 ✅

### Step 16: .gitignore 更新
- [x] 新增 data/llm_responses.db 至 .gitignore
- [x] SQLite 資料庫（含 organ_no 等資訊）不上傳

### Step 17: Git 分階段提交
- [x] 7 個 commit，按功能拆分：
  - feat: Phase 24 - 新增 LLM 回應儲存層
  - feat(prompt_builder): 新增 _metadata 參數
  - feat(llm_service): LLM 呼叫鏈串接 framework metadata
  - feat(graph): generate_node() 串接 prompt metadata
  - chore: .gitignore
  - chore: 統一 root logger 與敏感欄位保護
  - chore: 重構日誌輸出與 Phase 23 多樣化職責歸位

---

## 驗收標準

| 標準 | 說明 | 結果 |
|------|------|------|
| UT-03-01 | StorageInterface 必須是抽象類 | ✅ |
| UT-03-02 | save_response 必須是抽象方法 | ✅ |
| UT-03-03 | get_response 必須是抽象方法 | ✅ |
| UT-03-04 | list_by_organ 必須是抽象方法 | ✅ |
| UT-03-05 | 抽象類不能直接實例化 | ✅ |
| UT-05-01 | SQLiteStorage.save_response() 能保存 | ✅ |
| UT-05-02 | SQLiteStorage.get_response() 能取回 | ✅ |
| UT-05-03 | get_response() 不存在返回 None | ✅ |
| UT-05-04 | list_by_organ() 按機構列表 | ✅ |
| UT-05-05 | 數據一致性（保存後能完全取回） | ✅ |
| UT-07-01 | Factory.create("sqlite") 返回 SQLiteStorage | ✅ |
| UT-07-02 | create("unknown") 拋出 ValueError | ✅ |
| UT-07-03 | 空配置默認 SQLite | ✅ |
| UT-07-04 | 文件型 SQLite 可創建 | ✅ |
| IT-09-01 | 配置→工廠→存儲完整流程 | ✅ |
| IT-09-02 | save→get 完整流程 | ✅ |
| IT-09-03 | 所有字段數據一致性 | ✅ |
| ST-10 | llm_service.py 導入無錯誤 | ✅ |
| ST-12 | 18 欄位 schema（含 4 個 framework metadata） | ✅ |
| ST-13 | build_generate_prompt(_metadata={}) 回填 4 個 key | ✅ |
| ST-14 | _try_save_response() 寫入 4 個 framework key | ✅ |
| ST-15 | generate_node() 串接 _prompt_meta → call_llm() | ✅ |
| ST-16 | duration_ms 有值（不等於 NULL）| ✅ |
| ST-17 | 53/54 測試通過（1 個 pre-existing failure）| ✅ |

---

## Phase 24b: 錯誤日誌記錄

### 目標
- 記錄 API 錯誤到 DB（除錯與監控）
- 分離成功/錯誤資料表

### 完成項目

| 項目 | 說明 | 結果 |
|------|------|------|
| error_logs 表 | 11 個欄位 | ✅ |
| ErrorLog model | sqlite_adapter.py | ✅ |
| ErrorLogger 類別 | error_logger.py | ✅ |
| api_controller 更新 | 三處錯誤處理 | ✅ |
| 測試驗證 | ValidationError 寫入 | ✅ |

---

## 錯誤日誌 Schema

資料表：`error_logs`（共 11 欄位，儲存於 `data/llm_responses.db`）

| 欄位 | 類型 |說明 |
|------|------|------|
| `id` | INTEGER(PK) | 自動遞增 |
| `trace_id` | VARCHAR(INDEX) | 追蹤 ID |
| `organ_no` | VARCHAR(INDEX) | 統一編號 |
| `organ_name` | VARCHAR | 公司名稱 |
| `error_code` | VARCHAR(INDEX) | 錯誤代碼（例：SVC_001, INVALID_REQUEST） |
| `error_message` | TEXT | 錯誤訊息 |
| `error_phase` | VARCHAR | 錯誤階段（validation, external_service, api_gateway） |
| `recoverable` | INTEGER | 是否可復原（1=可復原，0=不可復原） |
| `request_payload` | TEXT | 請求 JSON |
| `mode` | VARCHAR | GENERATE / OPTIMIZE |
| `optimization_mode` | VARCHAR | CONCISE / STANDARD / DETAILED |
| `created_at` | VARCHAR(INDEX) | ISO8601 時間 |

---

## 新增檔案

| 檔案 | 類型 |
|------|------|
| `src/functions/utils/error_logger.py` | ErrorLogger 類別 |

---

## 測試結果

```
Error Logs (3 筆):
| trace_id | error_code | error_message | error_phase | recoverable |
|---------|-----------|-------------|------------|--------------|
| trace-94e55d... | INVALID_REQUEST | mode must be GENERATE | validation | 1 |
| test-999 | INVALID_REQUEST | mode must be GENERATE | validation | 1 |
| test-123 | SVC_001 | Test error | test | 1 |
```

---

## 備註

- Phase 24 從 Phase 23 延伸
- 雲端方案暫未定（DynamoDB/S3/PostgreSQL 接口已預留）
- 優先實作 SQLite（開發環境使用）
- 存儲失敗不影響主流程
- Phase 24b: 錯誤日誌記錄功能完成
- 版本 v0.4.1 ✅

## 文件清單

| 文件 | 類型 |
|------|------|
| `src/storage/__init__.py` | Package init |
| `src/storage/base.py` | 抽象層 (StorageInterface) |
| `src/storage/factory.py` | 工廠層 (StorageFactory) |
| `src/storage/sqlite_adapter.py` | SQLite 適配器 (LLMResponse + SQLiteStorage, 18 欄位) |
| `config/storage_config.json` | 儲存配置 |
| `src/functions/utils/llm_service.py` | LLM 呼叫層（含 storage hooks + framework metadata 寫入） |
| `src/functions/utils/prompt_builder.py` | Prompt 建構（含 _metadata 回填） |
| `src/langgraph_state/company_brief_graph.py` | LangGraph generate_node（wiring） |
| `src/functions/api_controller.py` | API 控制器（日誌統一化 + 敏感欄位遮蔽） |
| `src/functions/utils/structured_logger.py` | 結構化日誌（敏感欄位過濾） |
| `src/functions/utils/anomaly_detector.py` | 異常偵測（移除多餘 logging.basicConfig） |
| `src/functions/utils/post_processing.py` | 後處理（Phase 23 多樣化職責歸位） |
| `src/services/llm_service.py` | 備用 LLM Service（含 storage hooks，供 checkpoint2 測試） |
| `src/services/config_driven_search.py` | 配置驅動搜尋（print → logging.warning） |
| `src/services/config_loader.py` | 配置載入（移除重複 logging.basicConfig） |
| `.gitignore` | 新增 data/llm_responses.db |
| `tests/test_storage_base.py` | 抽象層單元測試 (5 用例) |
| `tests/test_sqlite_adapter.py` | SQLite 適配器單元測試 (5 用例) |
| `tests/test_storage_factory.py` | 工廠單元測試 (4 用例) |
| `tests/test_storage_integration.py` | 集成測試 (3 用例) |

---

## LLM 回應 Schema（最終版）

資料表：`llm_responses`（共 18 欄位，儲存於 `data/llm_responses.db`）

| 欄位 | 類型 |說明 |
|------|------|------|
| `request_id` | VARCHAR(PK) | 請求唯一識別 |
| `trace_id` | VARCHAR | 追蹤 ID |
| `organ_no` | VARCHAR(INDEX) | 統一編號 |
| `mode` | VARCHAR | GENERATE / OPTIMIZE |
| `prompt_raw` | TEXT | 原始 Prompt |
| `prompt_structure_key` | VARCHAR | Phase 23 框架 key（例：`data_oriented`） |
| `prompt_opening_key` | VARCHAR | Phase 23 開頭情境 key（例：`problem`） |
| `prompt_sentence_key` | VARCHAR | Phase 23 句型 key（例：`service`） |
| `prompt_template_name` | VARCHAR | 模板名稱（`concise` / `standard` / `detailed`） |
| `response_raw` | TEXT | 原始 LLM 回應 |
| `response_processed` | TEXT | 解析後的 JSON 字串 |
| `is_json` | INTEGER(0/1) | 是否為 JSON 格式 |
| `word_count` | INTEGER | 回應字數 |
| `tokens_used` | INTEGER | Token 消耗量 |
| `model` | VARCHAR | LLM 模型名稱 |
| `latency_ms` | INTEGER | API 回應延遲（毫秒）|
| `duration_ms` | INTEGER | 總處理時間（API + parsing，毫秒）|
| `created_at` | VARCHAR(INDEX) | ISO8601 建立時間 |

---

## 技術決策記錄

| 決策 | 選擇 | 理由 |
|------|------|------|
| 工廠 vs 註冊模式 | 工廠模式 | 封閉式，非插件架構 |
| Schema 位置 | 在 adapter 內 | 各 adapter 可獨立定義 |
| 連線設定 | 外部 config JSON | 環境切換不需改 code |
| 儲存失敗處理 | Async write + try-catch | 不影響主流程 |
| Framework metadata 注入 | _metadata dict 參數 | 向後相容，零破壞 |
| duration_ms 計算 | 含 parsing 時間 | 區分 API 延遲 vs 總處理時間 |

---

## Phase 24 vs Phase 23 整合

| 關注點 | Phase 23 | Phase 24 |
|--------|----------|----------|
| 模板名稱 | `TEMPLATE_DESCRIPTIONS` | → 寫入 `prompt_template_name` |
| 框架 key | `structure_library` 隨機選取 | → 寫入 `prompt_structure_key` |
| 開頭情境 key | `opening_library` 隨機選取 | → 寫入 `prompt_opening_key` |
| 句型 key | `sentence_library` 隨機選取 | → 寫入 `prompt_sentence_key` |

整合方式：Phase 24 **不修改** Phase 23 的任何邏輯，僅從 `build_generate_prompt()` 的輸出中**提取** framework 選取結果，寫入資料庫。

---

## Git 提交記錄

```
1aa5114  chore: 重構日誌輸出與 Phase 23 多樣化職責歸位
bbe0fe0  chore: 統一 root logger 配置與敏感欄位保護
bff5b71  chore: 新增 data/llm_responses.db 到 .gitignore
9dcb00a  feat(graph): generate_node() 串接 prompt metadata → call_llm()
593a4cc  feat(llm_service): LLM 呼叫鏈串接 Phase 23 framework metadata
23e02d1  feat(prompt_builder): 新增 _metadata 參數，回填 Phase 23 framework 選取結果
8f4e4ea  feat: Phase 24 - 新增 LLM 回應儲存層（Storage Layer）
e09b1db  feat: Phase 23 - 模板多樣化，透過 Prompt 更新與三個庫解決模板一致與句型僵化問題
```