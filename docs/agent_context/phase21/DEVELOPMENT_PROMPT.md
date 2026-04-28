# Phase 21 錯誤處理標準化 - 開發指令

**執行者**: Development Agent  
**參考文件**: `docs/phase21/DEVELOPMENT_PLAN.md`

---

## 任務目標

建立統一的錯誤處理機制，實現「集中式例外轉換」（Centralized Exception Translation），確保錯誤可追蹤、Client 能判斷是否成功、統一錯誤回應格式。

---

## 設計架構

```
各 node: catch → 建立 NodeResult（不拋出）
    ↓
generate_company_brief(): 統一檢查 state["errors"] → 翻譯並拋出
    ↓
Controller: 統一處理 → ResponseFactory.error()
```

---

## 執行步驟

### Step 1: 環境準備與現狀確認

**參考**: Phase 2-1 in DEVELOPMENT_PLAN.md

1. 確認所有相關程式碼在本地可用
2. 啟動 API server (`python scripts/test_api_server.py`)
3. 發送一筆正常請求確認功能正常
4. 發送一筆故意錯誤的請求觀察目前行為

**測試目標**: 
- API 可正常運作
- 確認目前錯誤行為（錯誤請求返回 `success: true` + 罐頭內容，這是不對的）

**完成標準**:
- [ ] API server 可啟動
- [ ] 正常請求可返回內容
- [ ] 觀察並記錄目前錯誤請求的回應行為

---

### Step 2: 實作 Task 1 - generate_company_brief() 錯誤檢查

**參考**: Phase 2-2 in DEVELOPMENT_PLAN.md

**檔案**: `src/langgraph_state/company_brief_graph.py`

**變更內容**:
在 `generate_company_brief()` 的 `graph.invoke()` 後，新增錯誤檢查邏輯：

```python
# 位置：在 final_state = self.compiled_graph.invoke(initial_state) 之後

# ===== 新增：檢查錯誤並拋出 =====
if final_state.get("errors"):
    first_error = final_state["errors"][0]
    from src.functions.utils.error_handler import ExternalServiceError
    raise ExternalServiceError(
        code=first_error.code or "SVC_001",
        message=first_error.error_message or "處理失敗"
    )
# ===============================
```

**測試目標**: 確認錯誤被拋出，不是被悶住

**預期結果**:
- Server 日誌出現 `ExternalServiceError`
- API 返回 500 錯誤

**完成標準**:
- [ ] 程式碼修改完成
- [ ] 錯誤被拋出到上層
- [ ] 日誌有錯誤記錄

---

### Step 3: 實作 Task 2 - generate_brief() 例外轉換

**參考**: Phase 2-3 in DEVELOPMENT_PLAN.md

**檔案**: `src/functions/utils/generate_brief.py`

**變更內容**:
在 `generate_brief()` 新增 try-catch，轉換 `ExternalServiceError` 為 `LLMServiceError`：

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

**測試目標**: 確認錯誤傳遞到 Controller 層

**預期結果**:
- Server 日誌出現 `LLMServiceError`

**完成標準**:
- [ ] 程式碼修改完成
- [ ] `LLMServiceError` 可被 Controller 捕捉

---

### Step 4: 實作 Task 3 - Controller 統一錯誤處理

**參考**: Phase 2-4 in DEVELOPMENT_PLAN.md

**檔案**: `src/functions/api_controller.py`

**變更內容**:
修改 `process_company_profile()` 的錯誤處理，使用 `ResponseFactory` 統一處理：

```python
from utils.error_handler import LLMServiceError, ExternalServiceError, ValidationError
from utils.responses import ResponseFactory

# 在 process_company_profile() 函式內的 except 區塊

except ValidationError as e:
    return jsonify(ResponseFactory.error(e.code, trace_id, str(e))), 400

except (ExternalServiceError, LLMServiceError) as e:
    return jsonify(ResponseFactory.error(
        code=e.code,
        message=e.message,
        retryable=e.retryable,
        retry_after=e.retry_after
    )), e.http_status if hasattr(e, 'http_status') else 500

except Exception as e:
    return jsonify(ResponseFactory.error("API_009", trace_id, str(e))), 500
```

**測試目標**: API 回應符合 ErrorResponse schema

**預期結果**:
- 回應包含 `success: false`
- 回應包含 `error.code`
- 回應包含 `error.message`
- 回應包含 `error.trace_id`

**完成標準**:
- [ ] 程式碼修改完成
- [ ] API 回應格式正確
- [ ] HTTP status code 正確

---

### Step 5: 整合測試

**參考**: Phase 2-5 in DEVELOPMENT_PLAN.md

**測試矩陣**:

| 測試案例 | 輸入 | 預期 HTTP Status | 預期 success | 預期 error.code |
|---------|------|-----------------|--------------|-----------------|
| 正常請求 | 有效公司名稱 | 200 | true | - |
| LLM 429 | 短時間多次請求 | 429 | false | LLM_001 |
| 搜尋超時 | 隨機公司名 | 500 | false | SCH_001 |
| 驗證失敗 | 缺少必要欄位 | 400 | false | API_002 |

**驗收標準**:
- [ ] 正常請求：`success: true`，內容正確
- [ ] LLM 429：`success: false`，`error.code: LLM_001`
- [ ] 搜尋超時：`success: false`，`error.code: SCH_001`
- [ ] 驗證失敗：`success: false`，`error.code: API_002`

---

### Step 6: 文件更新

**參考**: Phase 2-6 in DEVELOPMENT_PLAN.md

1. 更新 DEVELOPMENT_PLAN.md 為完成狀態（所有打勾完成）
2. 在 error_codes_and_schema.md 補充 Phase 21 變更說明

---

## 禁止事項

| 項目 | 禁止原因 |
|------|---------|
| **修改 node 內的 try-catch 邏輯** | 各 node 的 try-catch 保持現狀，只建立 NodeResult |
| **在每個 node 內拋出例外** | 錯誤傳遞集中在 `generate_company_brief()` 處理 |
| **修改 Phase 20 已完成的錯誤代碼** | 避免破壞現有定義 |
| **刪除現有錯誤處理邏輯** | 維持現有功能 |
| **修改 API 端點 URL** | 只修改錯誤處理，不改變 API 介面 |

---

## 驗收條件

1. **準確性**: 每種錯誤類型都返回正確的 error.code
2. **完整性**: 錯誤回應包含所有必要欄位（code、message、trace_id）
3. **一致性**: 所有錯誤類型的回應格式相同
4. **可追蹤性**: 日誌包含 request_id、trace_id

---

## 錯誤代碼參考

詳見 `docs/error_codes_and_schema.md`

| 錯誤類型 | 代碼 |
|---------|------|
| API 配額用盡 | LLM_001 |
| 處理逾時 | LLM_002 |
| 搜尋逾時 | SCH_001 |
| 驗證失敗 | API_002 |
| 未知錯誤 | LLM_008 |

---

**開始執行以上步驟，每個 Step 完成後匯報進度與結果。**