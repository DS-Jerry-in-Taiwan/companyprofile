# Phase 21: 錯誤處理標準化

## 狀態：✅ 完成

> 版本 1.6.0 (2026-04-23)

---

## 1. 問題分析

### 1.1 目前錯誤傳遞機制的問題

```
錯誤發生
    ↓
各 node 的 try/catch (search_node, summary_node, generate_node)
    ↓ 只建立 NodeResult(status=FAILED)，不回傳
    ↓ 不拋出例外
graph.invoke() 完成
    ↓
generate_company_brief() 返回 processed_result
    ↓ 不檢查 state["errors"]
Controller 收到的是「降級的預設內容」
Client 不知道發生了錯誤
```

### 1.2 錯誤傳遞鏈是斷的

| 環節 | 目前情況 |
|------|---------|
| 各 node 的 try-catch | ✅ 有，但**只建立 NodeResult，不拋出** |
| state["errors"] | 被填入，但**沒有人檢查** |
| generate_company_brief() | **不檢查** errors |
| Controller | **catch 不到**例外，因為沒有被拋出 |
| Client | 收到"罐頭內容"，**不知道是錯誤** |

### 1.3 觀察到的錯誤現象

```
[Pasted]
WARNING:src.langchain.error_handlers:[llm_call] 第 1 次嘗試失敗: UnknownError - LLM API call failed: 429 RESOURCE_EXHAUSTED
ERROR:src.langchain.error_handlers:[llm_call] 不可重試的錯誤: UnknownError
ERROR:src.functions.utils.llm_service:LLM call with retry failed: Non-retryable error: UnknownError
```

**問題**：
- `RESOURCE_EXHAUSTED` (429) 不被正確分類為「可重試」
- 錯誤被 `call_llm` 吃掉，返回預設罐頭內容
- API 回應內容空泛

---

## 2. 目標

### 2.1 正確的錯誤處理流程

```
各 node: try-catch → 建立 NodeResult
    ↓
generate_company_brief(): 統一檢查 state["errors"]
    ↓ 有錯誤 → raise ExternalServiceError(code="LLM_001", message="...")
    ↓
Controller: catch ExternalServiceError
    ↓
ResponseFactory.error(e.code) → JSON
```

### 2.2 達成的效果

| 效果 | 說明 |
|------|------|
| **錯誤可追蹤** | 有 error_code, error_message, trace_id |
| **Client 知道失敗** | API 回應 `success: false` |
| **統一錯誤格式** | 所有錯誤用相同 schema |
| **好維護** | 錯誤代碼集中在 `errors.py` 定義 |

---

## 3. 設計方案

### 3.1 錯誤處理架構：Centralized Exception Translation

```
各 node:  catch → 建立 NodeResult（不翻譯）
    ↓
單一轉換點: generate_company_brief() 檢查 errors → 翻譯並拋出
    ↓
Controller: 統一處理
```

### 3.2 Exception Mapping Pattern

| 層 | 責任 | 做法 |
|---|------|------|
| **各 node** | 捕捉錯誤、建立 NodeResult | 保持現有 try-catch，不拋出 |
| **generate_company_brief()** | 統一檢查並翻譯 | 檢查 `state["errors"]`，若有則 raise |
| **Controller** | 統一格式化 | `ResponseFactory.error(e.code, ...)` |

---

## 4. 錯誤代碼定義

### 4.1 已有的定義（Phase 20 產出）

參考 `docs/error_codes_and_schema.md`

```python
# API 錯誤
API_001 ~ API_012

# LLM 錯誤
LLM_001 (429 RESOURCE_EXHAUSTED) - 可重試
LLM_002 (504 Timeout) - 可重試
LLM_003 ~ LLM_008

# 搜尋錯誤
SCH_001 ~ SCH_005
```

### 4.2 待補充

- 錯誤訊息模板（目前只有代碼，訊息在 `ErrorCode` 枚舉）
- ErrorResponse schema（已完成）

---

## 5. 實作任務

### Task 1: 修改 generate_company_brief() 加入錯誤檢查

**位置**: `src/langgraph_state/company_brief_graph.py`

**變更**:
```python
def generate_company_brief(...):
    graph = create_company_brief_graph()
    final_state = graph.invoke(initial_state)

    # ===== 新增：檢查錯誤並拋出 =====
    if final_state.get("errors"):
        first_error = final_state["errors"][0]
        from src.functions.utils.error_handler import ExternalServiceError
        raise ExternalServiceError(
            code=first_error.code or "SVC_001",
            message=first_error.error_message or "處理失敗"
        )
    # ================================

    return processed_result
```

### Task 2: 修改 generate_brief() 轉換例外

**位置**: `src/functions/utils/generate_brief.py`

**變更**:
```python
def generate_brief(data):
    try:
        result = generate_company_brief(...)
        return {...}
    except ExternalServiceError as e:
        from src.functions.utils.error_handler import LLMServiceError
        raise LLMServiceError(
            code=e.code,
            message=e.message,
            retryable=e.recoverable
        )
```

### Task 3: 修改 Controller 統一處理

**位置**: `src/functions/api_controller.py`

**變更**:
```python
from utils.error_handler import LLMServiceError, ExternalServiceError, ValidationError
from utils.responses import ResponseFactory

except ValidationError as e:
    return jsonify(ResponseFactory.error(e.code, trace_id, str(e))), 400

except (ExternalServiceError, LLMServiceError) as e:
    return jsonify(ResponseFactory.error(
        code=e.code,
        message=e.message,
        retryable=e.retryable,
        retry_after=e.retry_after
    )), e.http_status if hasattr(e, 'http_status') else 500
```

### Task 4: 強化 classify_error() 處理 RESOURCE_EXHAUSTED

**位置**: `src/langchain/error_handlers.py` (已完成)

```python
def classify_error(error: Exception) -> str:
    error_str = str(error).lower()

    # Gemini API 429 RESOURCE_EXHAUSTED
    if "resource_exhausted" in error_str or "RESOURCE_EXHAUSTED" in str(error):
        return "HTTPError(429)"
    # ...
```

---

## 6. 變更範圍

| 檔案 | 變更 | 優先級 |
|------|------|--------|
| `src/langgraph_state/company_brief_graph.py` | 新增錯誤檢查並拋出 | P0 |
| `src/functions/utils/generate_brief.py` | 轉換例外 | P0 |
| `src/functions/api_controller.py` | 統一錯誤處理 | P0 |
| `src/functions/utils/error_handler.py` | 已部分完成，可擴充 | P1 |
| `src/langchain/error_handlers.py` | 已完成，無需變更 | - |
| `docs/error_codes_and_schema.md` | 更新文件 | P2 |

---

## 7. 測試驗證

### 7.1 測試案例

| 案例 | 狀態 | 結果 |
|------|------|------|
| LLM API 429 | ⚠️ 待實際觸發 | API 配額充足，未能觸發（10/30/50 並發請求） |
| 搜尋超時 | ✅ 已測試 | TimeoutError → SVC_002 映射正確 |
| SVC_001 (LLM API call failed) | ✅ 已驗證 | 作為 ExternalServiceError 預設 code |
| SVC_003 (Search no results) | ✅ 已驗證 | 定義存在，搜尋工具回傳空結果而非拋出錯誤 |
| SVC_004 (Summary generation failed) | ✅ 已實作 | error_handled=True 時拋出 SVC_004 |
| ErrorCode 枚舉完整性 | ✅ 已測試 | 全部 32 個錯誤代碼正確 |
| ErrorResponse schema | ✅ 已測試 | api_controller.py 使用 ErrorResponse.to_dict() 回傳 |
| 正常流程 | ✅ 已測試 | `success: true`, 正常內容 |
| ValidationError | ✅ 已測試 | Log level 為 INFO |
| 整合測試 | ✅ 已測試 | 8 個測試案例通過 |

### 7.2 驗證指標

| 指標 | 狀態 |
|------|------|
| 錯誤時 API 回應正確代碼 | ✅ |
| 錯誤時有 trace_id | ✅ |
| Client 能判斷是否成功 | ✅ |
| 日誌有完整錯誤追蹤 | ✅ |
| 搜尋超時錯誤處理 (SVC_002) | ✅ |
| 降級機制（aspect_summaries 為空時使用 user_input） | ✅ |
| SVC_004 錯誤拋出機制 | ✅ |
| ErrorResponse schema 回傳格式 | ✅ |

---

## 8. 依賴與順序

```
Phase 20 產出：
├── ErrorCode 枚舉 (error_handler.py)
├── ErrorResponse 格式
└── classify_error() 強化

Phase 21 實作：
├── Task 1: generate_company_brief() 錯誤檢查
├── Task 2: generate_brief() 轉換例外
└── Task 3: Controller 統一處理
```

---

## 9. 預計產出

| 產出 | 說明 |
|------|------|
| 錯誤處理標準文件 | `docs/error_codes_and_schema.md` |
| 錯誤代碼覆蓋率 | 90%+ 的錯誤有對應代碼 |
| 統一的 API 錯誤回應格式 | `ResponseFactory` |

---

## 10. 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 1.0.0 | 2026-04-21 | 初始規劃文件 |
| 1.1.0 | 2026-04-22 | 完成實作：錯誤傳遞到 Controller |
| 1.2.0 | 2026-04-22 | 新增：降級機制與 format_content() |
| 1.3.0 | 2026-04-23 | 附錄：Summary 流程調整 |
| 1.4.0 | 2026-04-23 | 修正：ValidationError log level 改為 INFO |
| 1.5.0 | 2026-04-23 | 完成：錯誤處理整合測試通過 8 個測試案例 |
| 1.6.0 | 2026-04-23 | 完成：搜尋超時測試（SVC_002） |
| 1.7.0 | 2026-04-23 | 完成：SVC_001/003/004 驗證（SVC_004 已實作） |
| 1.8.0 | 2026-04-23 | 修正：錯誤代碼統一使用 ErrorCode 枚舉 |
| 1.9.0 | 2026-04-23 | 修正：api_controller.py 使用 ErrorResponse schema 回傳錯誤 |
