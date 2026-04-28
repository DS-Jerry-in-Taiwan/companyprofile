# Phase 21: 錯誤處理標準化 - 階段開發文件

**版本**: 1.0.0  
**狀態**: 規劃中  
**日期**: 2026-04-21

---

## 1. 概述

### 1.1 目標

建立統一的錯誤處理機制，實現「集中式例外轉換」（Centralized Exception Translation），確保：
- 錯誤可追蹤（有 error_code、trace_id）
- Client 能判斷是否成功
- 統一錯誤回應格式
- 易於維護

### 1.2 設計架構

```
各 node: catch → 建立 NodeResult（不拋出）
    ↓
generate_company_brief(): 統一檢查 state["errors"] → 翻譯並拋出
    ↓
Controller: 統一處理 → ResponseFactory.error()
```

---

## 2. 逐步開發與測試步驟

### Phase 2-1: 環境準備與現狀確認

| 項目 | 內容 |
|------|------|
| **時機** | 正式開發前 |
| **開發動作** | 1. 確認所有相關程式碼在本地可用 <br> 2. 建立 API 測試環境 <br> 3. 確認 Flask server 可啟動 |
| **測試動作** | 1. 啟動 API server <br> 2. 發送一筆正常請求確認功能正常 <br> 3. 發送一筆故意錯誤的請求觀察目前行為 |
| **測試目標** | API 可正常運作，確認目前錯誤行為 |
| **預期結果** | - 正常請求返回成功內容 <br> - 錯誤請求返回罐頭內容，`success: true`（這是不對的） |
| **產出文件** | 測試截圖/日誌記錄 |

**完成標準**：
- [ ] API server 可啟動
- [ ] 正常請求可返回內容
- [ ] 觀察並記錄目前錯誤請求的回應行為

---

### Phase 2-2: 實作 Task 1 - generate_company_brief() 錯誤檢查

| 項目 | 內容 |
|------|------|
| **時機** | Phase 2-1 完成後 |
| **開發動作** | 在 `generate_company_brief()` 的 `graph.invoke()` 後，新增錯誤檢查邏輯：<br><br>```python<br>final_state = graph.invoke(initial_state)<br><br># 檢查錯誤<br>if final_state.get("errors"):<br>    first_error = final_state["errors"][0]<br>    raise ExternalServiceError(<br>        code=first_error.code or "SVC_001",<br>        message=first_error.error_message or "處理失敗"<br>    )<br>``` |
| **測試動作** | 1. 重啟 API server <br> 2. 發送會觸發錯誤的請求（如：空白公司名稱） <br> 3. 檢查 server 日誌 |
| **測試目標** | 確認錯誤被拋出，不是被悶住 |
| **預期結果** | - Server 日誌出現 `ExternalServiceError` <br> - API 返回 500 錯誤 |
| **產出文件** | 修改的程式碼片段、測試截圖 |

**完成標準**：
- [ ] 程式碼修改完成
- [ ] 錯誤被拋出到上層
- [ ] 日誌有錯誤記錄

---

### Phase 2-3: 實作 Task 2 - generate_brief() 例外轉換

| 項目 | 內容 |
|------|------|
| **時機** | Phase 2-2 完成後 |
| **開發動作** | 在 `generate_brief()` 新增 try-catch，轉換 `ExternalServiceError` 為 `LLMServiceError`：<br><br>```python<br>try:<br>    result = generate_company_brief(...)<br>    return {...}<br>except ExternalServiceError as e:<br>    raise LLMServiceError(<br>        code=e.code,<br>        message=e.message,<br>        retryable=e.recoverable<br>    )<br>``` |
| **測試動作** | 1. 發送會觸發錯誤的請求 <br> 2. 檢查 server 日誌 |
| **測試目標** | 確認錯誤傳遞到 Controller 層 |
| **預期結果** | - Server 日誌出現 `LLMServiceError` |
| **產出文件** | 修改的程式碼片段 |

**完成標準**：
- [ ] 程式碼修改完成
- [ ] `LLMServiceError` 可被 Controller 捕捉

---

### Phase 2-4: 實作 Task 3 - Controller 統一錯誤處理

| 項目 | 內容 |
|------|------|
| **時機** | Phase 2-3 完成後 |
| **開發動作** | 修改 `api_controller.py`，使用 `ResponseFactory` 統一處理錯誤：<br><br>```python<br>from utils.error_handler import LLMServiceError, ExternalServiceError, ValidationError<br>from utils.responses import ResponseFactory<br><br>except ValidationError as e:<br>    return jsonify(ResponseFactory.error(e.code, trace_id, str(e))), 400<br><br>except (ExternalServiceError, LLMServiceError) as e:<br>    return jsonify(ResponseFactory.error(<br>        code=e.code,<br>        message=e.message,<br>        retryable=e.retryable,<br>        retry_after=e.retry_after<br>    )), e.http_status if hasattr(e, 'http_status') else 500)<br>``` |
| **測試動作** | 1. 發送不同類型的錯誤請求 <br> 2. 檢查 API 回應格式 |
| **測試目標** | API 回應符合 ErrorResponse schema |
| **預期結果** | - 回應包含 `success: false` <br> - 回應包含 `error.code` <br> - 回應包含 `error.message` <br> - 回應包含 `error.trace_id` |
| **產出文件** | 修改的程式碼片段 |

**完成標準**：
- [ ] 程式碼修改完成
- [ ] API 回應格式正確
- [ ] HTTP status code 正確

---

### Phase 2-5: 整合測試

| 項目 | 內容 |
|------|------|
| **時機** | Phase 2-4 完成後 |
| **開發動作** | 無（僅測試） |
| **測試動作** | 1. 正常請求測試 <br> 2. LLM 429 錯誤測試 <br> 3. 搜尋超時測試 <br> 4. 驗證錯誤測試 |
| **測試目標** | 所有錯誤場景都能正確處理 |
| **預期結果** | 見下方「測試矩陣」 |

**完成標準**：
- [ ] 正常請求：`success: true`，內容正確
- [ ] LLM 429：`success: false`，`error.code: LLM_001`
- [ ] 搜尋超時：`success: false`，`error.code: SCH_001`
- [ ] 驗證失敗：`success: false`，`error.code: API_002`

---

### Phase 2-6: 文件更新

| 項目 | 內容 |
|------|------|
| **時機** | 所有開發測試完成後 |
| **開發動作** | 1. 更新本開發文件為完成狀態 <br> 2. 更新 error_codes_and_schema.md <br> 3. 更新架構圖 |
| **測試動作** | 無 |
| **測試目標** | 文件齊全 |
| **產出文件** | - Phase 21 README.md（更新為完成狀態） <br> - error_codes_and_schema.md（補充 Phase 21 變更） |

**完成標準**：
- [ ] 所有完成項目打勾
- [ ] 變更記錄更新

---

## 3. 各步驟的測試目標與標準

### 3.1 測試矩陣

| 測試案例 | 輸入 | 預期 HTTP Status | 預期 success | 預期 error.code | 預期 error.message |
|---------|------|-----------------|--------------|-----------------|-------------------|
| 正常請求 | 有效公司名稱 | 200 | true | - | - |
| LLM 429 | 短時間多次請求 | 429 | false | LLM_001 | "API 配額已用盡..." |
| 搜尋超時 | 隨機公司名 | 500 | false | SCH_001 | "搜尋逾時..." |
| 驗證失敗 | 缺少必要欄位 | 400 | false | API_002 | "缺少必要欄位..." |
| 其他錯誤 | 任意 | 500 | false | LLM_008 | "發生未知錯誤..." |

### 3.2 驗收標準

| 標準 | 說明 |
|------|------|
| **準確性** | 每種錯誤類型都返回正確的 error.code |
| **完整性** | 錯誤回應包含所有必要欄位（code、message、trace_id） |
| **一致性** | 所有錯誤類型的回應格式相同 |
| **可追蹤性** | 日誌包含 request_id、trace_id |

---

## 4. 各步驟完成後要紀錄與更新的文件

| 步驟 | 需紀錄/更新 |
|------|------------|
| Phase 2-1 | - 測試截圖 <br> - 目前行為描述 |
| Phase 2-2 | - 程式碼變更（company_brief_graph.py） <br> - 測試截圖/日誌 |
| Phase 2-3 | - 程式碼變更（generate_brief.py） <br> - 測試截圖/日誌 |
| Phase 2-4 | - 程式碼變更（api_controller.py） <br> - API 回應範例 |
| Phase 2-5 | - 測試結果矩陣 <br> - 失敗案例分析（若有） |
| Phase 2-6 | - 最終版 README.md <br> - error_codes_and_schema.md 更新 |

---

## 5. 開發與測試的任務邊界

### 5.1 開發邊界（负责範圍）

| 元件 | 開發者職責 |
|------|-----------|
| `company_brief_graph.py` | 新增錯誤檢查並拋出例外 |
| `generate_brief.py` | 例外轉換 |
| `api_controller.py` | 統一錯誤處理 |
| `error_handler.py` | （已存在，確保可用） |
| `responses.py` | （已存在，確保可用） |

### 5.2 測試邊界（負責範圍）

| 項目 | 測試者職責 |
|------|-----------|
| API 功能測試 | 發送 HTTP 請求，驗證回應 |
| 錯誤場景測試 | 觸發各類錯誤，驗證正確處理 |
| 效能測試 | （可選）確認錯誤處理不影響效能 |

### 5.3 外部依賴（不在本次開發範圍）

| 項目 | 說明 |
|------|------|
| LLM API | 不需修改，只觸發錯誤 |
| 搜尋工具 | 不需修改，只觸發錯誤 |
| 前端 | 不需修改 |
| 其他 API | 不需修改 |

---

## 6. 禁止事項

### 6.1 開發過程禁止

| 項目 | 禁止原因 |
|------|---------|
| **修改 node 內的 try-catch 邏輯** | 各 node 的 try-catch 保持現狀，只建立 NodeResult |
| **在每個 node 內拋出例外** | 錯誤傳遞集中在 `generate_company_brief()` 處理 |
| **修改 Phase 20 已完成的錯誤代碼** | 避免破壞現有定義 |
| **刪除現有錯誤處理邏輯** | 維持現有功能 |
| **修改 API 端點 URL** | 只修改錯誤處理，不改變 API 介面 |

### 6.2 測試過程禁止

| 項目 | 禁止原因 |
|------|---------|
| **大量請求觸發 DDoS** | 避免被API暫時封鎖 |
| **修改測試資料庫** | 保持測試環境乾淨 |
| **跳過任何測試步驟** | 確保每階段都正確 |

---

## 7. 風險與對應

| 風險 | 影響 | 對應方式 |
|------|------|---------|
| 429 錯誤頻繁觸發 | 測試無法進行 | 使用單次請求測試，間隔 30 秒 |
| 錯誤被悶住仍未拋出 | 功能無效 | Phase 2-2 先驗證日誌 |
| ResponseFactory 缺少欄位 | 回應不完整 | 提前確認 ResponseFactory 可用 |

---

## 8. 進度追蹤

| 步驟 | 狀態 | 開始日期 | 結束日期 | 備註 |
|------|------|----------|----------|------|
| Phase 2-1 | ✅ 完成 | - | 2026-04-22 | |
| Phase 2-2 | ✅ 完成 | 2026-04-22 | 2026-04-22 | |
| Phase 2-3 | ✅ 完成 | 2026-04-22 | 2026-04-22 | |
| Phase 2-4 | ✅ 完成 | 2026-04-22 | 2026-04-22 | |
| Phase 2-5 | ✅ 完成 | 2026-04-22 | 2026-04-22 | |
| Phase 2-6 | ✅ 完成 | 2026-04-22 | 2026-04-22 | |
| 搜尋超時測試 | ✅ 完成 | 2026-04-23 | 2026-04-23 | Mock TimeoutError 測試通過 |
| SVC_001/003/004 測試 | ✅ 完成 | 2026-04-23 | 2026-04-23 | SVC_004 已實作 |
| LLM 429 測試 | ⚠️ 待測試 | - | - | API 配額充足，未能觸發 |

---

## 10. 新流程設計 - 降級機制

### 10.1 設計原則

1. **有搜尋結果** → 用 aspect_summaries 生成
2. **無搜尋結果** → 用 user_input 生成
3. **無搜尋結果 + 無 user_input** → 報錯

### 10.2 field → aspect mapping

```python
FIELD_TO_ASPECT = {
    "unified_number": "foundation",
    "capital": "foundation",
    "founded_date": "foundation",
    "address": "foundation",
    "officer": "vibe",
    "main_services": "core",
    "business_items": "core",
}
```

### 10.3 format_content() - 自動判斷格式

```python
def format_content(data):
    if "foundation" in data or "core" in data:
        # aspect 格式
        for key, value in data.items():
            if value:
                parts.append(f"【{key}】\n{value}")
    else:
        # user_input 格式
        for key, value in data.items():
            if value:
                parts.append(f"{key}：{value}")
    return "\n".join(parts)
```

### 10.4 完整流程圖

```
┌─────────────────────────────────────────────────────────────┐
│ search_node                                                │
│  搜尋公司資訊                                              │
│  輸出：search_result (answer + results)                   │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │   summary_node     │
            │   field → aspect  │
            │   mapping         │
            │   (不會報錯)       │
            └──────────┬────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ route_after_summary│
            │ → generate_node    │
            └──────────┬────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ generate_node                                              │
│  用 aspect_summaries 生成                                 │
│  如果 aspect_summaries 為空 → 用 user_input 生成          │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ quality_check_node │
            └──────────┬────────┘
                       │
                       ▼
                       END
```

### 10.5 降級機制表

| 情況 | aspect_summaries | user_input | web_content |
|------|-----------------|------------|-------------|
| 有搜尋結果 | ✅ 有（部分或全部） | 有/無 | 用 aspect_summaries |
| 無搜尋結果 | ❌ 空 | ✅ 有 | 用 user_input |
| 無搜尋結果 + 無 user_input | ❌ 空 | ❌ 無 | 報錯 |

### 10.6 節點職責

| 節點 | 職責 | 會報錯嗎 |
|------|------|---------|
| search_node | 搜尋公司資訊 | ✅ 可能 |
| summary_node | field → aspect mapping | ❌ 不會 |
| generate_node | 生成簡介 | ✅ 可能 |
| quality_check_node | 品質檢查 | ❌ 不會 |
| error_handler_node | 降級處理 | - |

---

## 11. 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 1.0.0 | 2026-04-21 | 初始規劃 |
| 1.1.0 | 2026-04-22 | 完成實作：錯誤傳遞到 Controller |
| 1.2.0 | 2026-04-22 | 新增：降級機制與 format_content() |
| 1.3.0 | 2026-04-23 | 附錄：Summary 流程調整（見 DEVELOPMENT_PLAN_SUMMARY.md） |
| 1.4.0 | 2026-04-23 | 修正：ValidationError log level 改為 INFO，移除"驗證錯誤" prefix |
| 1.5.0 | 2026-04-23 | 完成：錯誤處理整合測試通過 8 個測試案例 |
| 1.6.0 | 2026-04-23 | 完成：搜尋超時測試（SVC_002） |
| 1.7.0 | 2026-04-23 | 完成：SVC_001/003/004 驗證（SVC_004 已實作） |
| 1.8.0 | 2026-04-23 | 修正：錯誤代碼統一使用 ErrorCode 枚舉（company_brief_graph.py, llm_service.py） |
| 1.9.0 | 2026-04-23 | 修正：api_controller.py 使用 ErrorResponse schema 回傳錯誤 |

---

## 12. 附錄：降級機制實作

詳細實作內容請參考 `DEVELOPMENT_PLAN_SUMMARY.md`