# Phase 23 開發紀錄

## 版本
- **文件版本**: v0.2.1
- **建立日期**: 2026-04-23
- **最後更新**: 2026-04-24
- **目標版本**: v0.3.9

---

## 開發日誌

### 📅 2026-04-23

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| - | 分析 v0.2.0 建議 | ✅ | 模板過於一致、句型僵化 |
| - | 討論框架設計 | ✅ | 句型庫 + 模板庫 |
| - | 討論寫作框架層級 | ✅ | 文章/段落/語句框架 |
| - | 確認框架套用流程 | ✅ | 產業→資訊→框架組合 |
| - | 建立 DEVELOPMENT_PLAN.md | ✅ | v0.2.0 |
| - | 建立 DEVELOPMENT_PLAN_DETAIL.md | ✅ | 詳細實作計劃 |
| - | 建立 TEST_METRICS.md | ✅ | 測試指標 |
| - | 建立 TASK_BOUNDARIES.md | ✅ | 任務邊界 |
| - | 建立 DEVELOPMENT_LOG.md | ✅ | 開發日誌 |
| - | 建立 DEVELOPER_PROMPT.md | ✅ | 開發者 Prompt |
| 2026-04-24 01:45 | **Phase 23a Step 1**: 修改 generate_prompt_template.txt | ✅ | 加入開頭多樣化、段落結構多樣化、句型變化原則 |
| 2026-04-24 01:45 | **Phase 23a Step 2**: 修改 optimize_prompt_template.txt | ✅ | 加入開頭多樣化、段落結構多樣化原則 |
| 2026-04-24 01:46 | **Phase 23a Step 3**: 建立驗證測試 test_phase23_prompt.py | ✅ | UT-01~UT-04 全部通過（5/5）|
| 2026-04-24 01:47 | **Phase 23b Step 4**: 建立 structure_library.py（文章框架庫）| ✅ | 6 種框架：traditional, service_first, value_first, future_oriented, feature_first, data_oriented |
| 2026-04-24 01:47 | **Phase 23b Step 5**: 加入情境庫 | ✅ | 5 種情境：industry, market, problem, trend, user |
| 2026-04-24 01:47 | **Phase 23b Step 6**: 加入句型庫 | ✅ | 7 種句型：service, feature, data, question, situation, achievement, commitment |
| 2026-04-24 01:48 | **Phase 23b Step 7**: 整合 post_processing.py | ✅ | 加入 structure_library 匯入與日誌記錄 |
| 2026-04-24 01:49 | 建立單元測試 test_structure_library.py | ✅ | 34 項測試全部通過 |
| 2026-04-24 01:50 | 建立整合測試 test_structure_diversification.py | ✅ | 6 項測試全部通過 |
| 2026-04-24 01:52 | 執行回歸測試 | ✅ | test_content_diversifier (28/28), test_markdown_cleaner (14/14), test_markdown_cleanup, test_svc_errors 全部通過 |

### 📅 2026-04-24（API 整合驗證）

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| 2026-04-24 02:50 | 執行 API 整合測試（3 次） | ✅ | 開頭多樣化 PASSED (3/3 不同) |

### API 驗證結果

| 驗證項目 | 標準 | 實際結果 |
|----------|------|----------|
| 開頭多樣化 | >= 2 種不同 | ✅ **3 種不同** |
| 段落流向多樣化 | >= 2 種不同 | ⚠️ 解析問題 |

**三個不同開頭示例**：
1. 「在全球半導體產業鏈中...」
2. 「面對全球科技產業對高效能...」
3. 「在人工智慧與高效能運算...」

全部**不是**「成立於」，而是**問題情境導向**！

| 時間 | 事項 | 狀態 | 備註 |
|------|------|------|------|
| 2026-04-24 14:30 | 根因分析：Phase 23 selection-only 問題 | ✅ | 發現選取的模板只在 post_processing.py 記錄日誌，從未傳入 LLM Prompt |
| 2026-04-24 14:45 | 建立 IMPLEMENTATION_SPEC_V0.2.0.md | ✅ | 完成標準、通過標準、失敗條件明確定義 |
| 2026-04-24 14:50 | 建立 VERIFICATION_STANDARD.md | ✅ | 區分單元測試 vs 實際驗證 |
| 2026-04-24 14:55 | 建立 DEVELOPER_PROMPT_V0.2.0.md | ✅ | Step-by-step 實作計劃 |
| 2026-04-24 15:00 | **v0.2.0 核心實現**：修改 prompt_builder.py | ✅ | 新增 `build_diversity_guide()`、`STRUCTURE_FLOW_DESCRIPTIONS`、`OPENING_DESCRIPTIONS`、`SENTENCE_DESCRIPTIONS` 常數；`build_generate_prompt()` 自動隨機選取並注入多樣化指導區塊 |
| 2026-04-24 15:05 | 修改 post_processing.py | ✅ | 移除 selection-only 日誌，改為 debug 註解（Phase 23 已改為 Prompt-level） |
| 2026-04-24 15:10 | 隨機性驗證 | ✅ | 5 次呼叫覆蓋 3 種框架、4 種開頭、4 種句型 |
| 2026-04-24 15:15 | 確認 generate_prompt_template.txt 不用修改 | ✅ | 發現此檔案由舊路徑 `src/services/llm_service.py` 使用；LangGraph 使用 `build_generate_prompt()` 程式化組裝 Prompt |
| 2026-04-24 15:30 | 建立 test_phase23_actual_verification.py | ✅ | Mock 模式 + API 模式雙模式驗證腳本 |
| 2026-04-24 15:35 | 執行 Mock 模式驗證（10 次） | ✅ | 框架 5/6 種 ✅、開頭 4/5 種 ✅、句型 5/7 種 ✅、非全部相同 ✅ → ALL PASSED |
| 2026-04-24 15:40 | 執行全部單元測試回歸 | ✅ | 34 項 structure_library 測試 PASS（詳見下方）|
| 2026-04-24 15:45 | 更新 DEVELOPMENT_LOG.md | ✅ | 加入 v0.2.0 開發紀錄 |

---

## v0.2.0 重新實現細節

### 問題根因（v0.1.0）

Phase 23 v0.1.0 只做到「選擇模板」+「記錄日誌」：
- `post_processing.py` 中呼叫 `get_random_structure()`、`get_random_opening()`、`get_random_sentence_pattern()`
- 僅 `logger.info()` 記錄選取的 key
- **選取的模板從未傳入 Prompt**，導致 LLM 生成時完全不知道這些模板存在
- 結果：每次輸出都完全一樣，問題未解決

### 解決方案（v0.2.0：Prompt 傳遞方式）

改為將選取的模板**注入 LLM Prompt**，讓 LLM 在生成時參考：

1. **在 prompt_builder.py 新增多樣化指導常數**：
   - `STRUCTURE_FLOW_DESCRIPTIONS`：框架段落順序說明（6 種）
   - `OPENING_DESCRIPTIONS`：開頭風格說明（5 種）
   - `SENTENCE_DESCRIPTIONS`：句型風格說明（7 種）

2. **新增 `build_diversity_guide()` 函式**：
   - 建構「結構與風格多樣化指導」區塊
   - 包含框架指導、開頭指導、句型指導、執行要求

3. **修改 `build_generate_prompt()`**：
   - 自動隨機選取 structure_key/opening_key/sentence_key（若未傳入）
   - 在 Prompt 末尾附加多樣化指導區塊
   - 記錄日誌：`[Phase23] Prompt 注入多樣化指導: 框架=xxx, 開頭=xxx, 句型=xxx`

4. **修改 post_processing.py**：
   - 移除 selection-only 日誌
   - 改為 debug 註解：Phase 23 已移至 Prompt-level

### 實現位置

```
build_generate_prompt() → 自動隨機選取 → build_diversity_guide() → 注入 Prompt → LLM 生成
```

### 驗證結果

| 驗證項目 | 標準 | 結果 |
|----------|------|------|
| 框架多樣化 | 覆蓋 >= 3 種 | ✅ 5/6 種 |
| 開頭多樣化 | 覆蓋 >= 2 種 | ✅ 4/5 種 |
| 句型多樣化 | 覆蓋 >= 3 種 | ✅ 5/7 種 |
| 非全部相同 | 不應全部相同 | ✅ 最長連續 3 次 |

### 架構發現

- `src/functions/generate_prompt_template.txt` **不由 LangGraph 使用**
- 該檔案由 `src/services/llm_service.py`（舊路徑）使用
- LangGraph 路徑：`company_brief_graph.py` → `generate_node()` → `build_generate_prompt()`（程式化組裝）
- 因此 **不需要修改 `generate_prompt_template.txt`**，多樣化指導直接在 Python 中注入

---

## 討論記錄

### 框架套用流程（共識）

```
1. 產業分類粗篩
   ↓ industry 分類
   → 排除不適用的框架
   
2. 取得資訊
   ↓ search 完成
   → 根據取得資訊決定框架複雜度
   
3. 框架組合（可隨機）
   ↓ 從剩下適合的框架中隨機選擇
   → 段落框架 + 語句框架 組合
   
4. （未來）風格樣本
   → 可加入 Few-shot 範例
```

### 三個庫（共識）

| 庫 | 用途 | 數量 |
|------|------|------|
| **文章框架庫** | 段落順序多樣化 | 6 種 |
| **情境庫** | 開頭情境描述 | 5 種 |
| **句型庫** | 句型多樣化 | 5+ 種 |

---

## 步驟追蹤

### Phase 23a: Prompt 更新
- [x] Step 1: 修改 generate_prompt_template.txt
- [x] Step 2: 修改 optimize_prompt_template.txt
- [x] Step 3: 整合測試

### Phase 23b: 模板庫實作
- [x] Step 4: 建立文章框架庫
- [x] Step 5: 建立情境庫
- [x] Step 6: 建立句型庫
- [x] Step 7: 整合後處理模組

---

## 程式碼變更紀錄

### 新增檔案（規劃）

| 檔案 | 用途 |
|------|------|
| `docs/agent_context/phase23/DEVELOPMENT_PLAN.md` | 規劃概覽 |
| `docs/agent_context/phase23/DEVELOPMENT_PLAN_DETAIL.md` | 詳細實作計劃 |
| `docs/agent_context/phase23/TEST_METRICS.md` | 測試指標 |
| `docs/agent_context/phase23/TASK_BOUNDARIES.md` | 任務邊界 |

### 新增檔案（實作完成）

| 檔案 | 用途 |
|------|------|
| `src/functions/utils/structure_library.py` | 模板庫實作（文章框架庫 6 種 + 情境庫 5 種 + 句型庫 7 種）|
| `tests/test_structure_library.py` | 34 項單元測試 |
| `scripts/test_phase23_prompt.py` | Prompt 驗證測試（UT-01~UT-04）|
| `scripts/test_structure_diversification.py` | 模板多樣化整合測試（6 項）|
| `scripts/test_phase23_actual_verification.py` | Mock + API 雙模式驗證腳本 |
| `docs/agent_context/phase23/IMPLEMENTATION_SPEC_V0.2.0.md` | 完成標準與失敗條件定義 |
| `docs/agent_context/phase23/VERIFICATION_STANDARD.md` | 單元測試 vs 實際驗證區分 |
| `docs/agent_context/phase23/DEVELOPER_PROMPT_V0.2.0.md` | Step-by-step 實作計劃 |

### 修改檔案（實作完成）

| 檔案 | 變更 |
|------|------|
| `src/functions/generate_prompt_template.txt` | 加入撰寫原則 5-7（開頭多樣化、段落結構多樣化、句型變化）|
| `src/functions/optimize_prompt_template.txt` | 加入優化指令 5-6（開頭多樣化、段落結構多樣化）|
| `src/functions/utils/post_processing.py` | 加入 Phase 23 structure_library 匯入與日誌（v0.1.0）；**v0.2.0 改為 debug 註解** |
| **`src/functions/utils/prompt_builder.py`** | **v0.2.0 核心**：新增多樣化指導常數、`build_diversity_guide()`、`build_generate_prompt()` 自動注入 |

---

## 問題與解決

| 日期 | 問題 | 解決方案 |
|------|------|----------|
| 2026-04-24 | API 429 RESOURCE_EXHAUSTED | Mock 模式驗證 Prompt 注入正確性；API 配額恢復後需重新執行實際驗證 |
| 2026-04-24 | v0.1.0 selection-only 未應用 | v0.2.0 改為 Prompt 傳遞方式，直接注入多樣化指導 |
| 2026-04-24 | LLM 回應未完整存儲 | v0.2.1 新增存儲設計 |

---

## LLM 回應存儲設計 (v0.2.1)

### 背景

- LLM 原始回應僅存於日誌（`app_structured.log`），最多 500 字符
- 需要完整存儲以支持：調試排查、數據分析、合規審計

### 部署架構考量

| 環境 | 存儲方案 | 原因 |
|------|----------|------|
| **開發環境** | SQLite | 本地開發、零成本、快速迭代 |
| **雲端部署 (Lambda)** | DynamoDB | 無服務器、按需擴展、Lambda 原生兼容 |

### Lambda 本地存儲限制

- ❌ 不能寫本地文件（tmp 是臨時的，每次執行後丟失）
- ❌ 不能依賴本地磁盤
- ❌ 本地文件會在 executions 之間丟失

### Schema 設計

#### SQLite (開發環境)

```sql
CREATE TABLE IF NOT EXISTS llm_responses (
    request_id TEXT PRIMARY KEY,
    trace_id TEXT,
    organ_no TEXT,
    mode TEXT CHECK(mode IN ('DETAILED', 'BRIEF')),
    
    -- Prompt
    prompt_raw TEXT,
    prompt_with_guidance TEXT,
    
    -- Response
    response_raw TEXT,
    response_processed TEXT,
    is_json INTEGER DEFAULT 0,
    word_count INTEGER,
    tokens_used INTEGER,
    model TEXT,
    latency_ms INTEGER,
    
    -- Metadata
    created_at TEXT,
    duration_ms INTEGER
);

CREATE INDEX idx_organ_no ON llm_responses(organ_no);
CREATE INDEX idx_created_at ON llm_responses(created_at);
```

#### 雲端存儲（預留接口）

- 方案未定（S3/DynamoDB/RDS 皆可能）
- 僅預留 `StorageInterface`，暫不實作具體適配器

### 存儲流程

```
LLM 調用 → 保存原始 response → post-processing → 返回
```

### 代碼分層設計

```python
# storage/base.py - 抽象接口
class StorageInterface:
    """存儲抽象接口"""
    def save_response(self, item: dict) -> bool: ...
    def get_response(self, request_id: str) -> Optional[dict]: ...
    def list_by_organ(self, organ_no: str) -> list[dict]: ...

# storage/factory.py - 工廠 + 配置層
class StorageFactory:
    """統一入口，通過配置創建適配器"""
    @staticmethod
    def create(config: dict) -> StorageInterface:
        storage_type = config.get("type", "sqlite")
        if storage_type == "sqlite":
            return SQLiteStorage(config.get("db_path"))
        elif storage_type == "dynamodb":
            return DynamoDBStorage(config.get("table_name"))
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
```

### 配置範例

```python
# 可放於 config/search_config.json 或新增 config/storage_config.json
{
  "storage": {
    "development": {
      "type": "sqlite",
      "db_path": "data/llm_responses.db"
    },
    "production": {
      "type": "dynamodb",  # 預留，等雲端方案確定
      "table_name": "LLM_Responses"
    }
  },
  "default": "development"
}
```

---

### ⚠️ 雲端部署注意

- **Lambda 不能寫本地文件**，需使用 S3/DynamoDB 等雲端存儲
- 開發環境用 SQLite，本地測試通過後再切換雲端方案

---

## 待完成事項

| 事項 | 優先級 | 備註 |
|------|--------|------|
| 建立 storage/ 目錄與抽象層 | 高 | StorageInterface + 配置層 |
| SQLite 適配器實作 | 高 | 開發環境 |
| LLM 服務層集成存儲 | 高 | llm_service.py 保存原始 response |
| DynamoDB 適配器預留 | 低 | 雲端方案未定，僅預留接口 |

---

## 備註

- Phase 23 ✅ 已結案 (v0.2.1)
- Phase 23 v0.2.1 新增：LLM 回應存儲設計（移至 Phase 24）
- **雲端方案暫未定**，DynamoDB/S3/RDS 皆可能
- 存儲失敗不應影響主流程
- Phase 23 預估時間：3 小時
- 前置條件：Phase 22 完成（v0.3.7）
- 相關問題：v0.2.0 建議 #2、#3
- 版本目標：v0.3.9

---

## Phase 23 結案狀態

| 項目 | 狀態 |
|------|------|
| **模板多樣化** | ✅ 已完成 |
| **v0.2.0 Prompt 注入方式** | ✅ 已完成 |
| **單元測試 34 項** | ✅ 全部通過 |
| **整合測試** | ✅ 通過 |
| **回歸測試** | ✅ 通過 |
| **存儲設計** | ⚠️ 移至 Phase 24 |

### Phase 23 完成時間
- **結案日期**: 2026-04-24
- **最終版本**: v0.2.1
- **目標版本達成**: v0.3.9 ✅