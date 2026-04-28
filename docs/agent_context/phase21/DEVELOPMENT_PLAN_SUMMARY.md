# Phase 21 附錄：Summary 流程調整 - 降級機制

**版本**: 1.0.0  
**狀態**: 規劃中  
**日期**: 2026-04-23

---

## 1. 概述

### 1.1 目標

實作降級機制與 format_content()，確保：
- 搜尋結果能正確映射到 aspect（field → aspect mapping）
- 當 aspect_summaries 為空時，能使用 user_input 生成簡介
- prompt builder 能自動判斷內容格式，只給有值的內容

### 1.2 設計架構

```
search_node → summary_node (field → aspect mapping) → 
generate_node (用 aspect_summaries 或 user_input 生成) →
quality_check_node → END
```

### 1.3 降級機制表

| 情況 | aspect_summaries | user_input | 行為 |
|------|-------------------|------------|------|
| 有搜尋結果 | ✅ 有（部分或全部） | 有/無 | 用 aspect_summaries 生成 |
| 無搜尋結果 | ❌ 空 | ✅ 有 | 用 user_input 生成 |
| 無搜尋結果 + 無 user_input | ❌ 空 | ❌ 無 | 報錯 |

---

## 2. 實作與測試步驟

### Step 1: 環境準備與現狀確認

**時機**: 正式開發前

**開發動作**:
1. 確認所有相關程式碼在本地可用
2. 啟動 API server (`python scripts/test_api_server.py`)
3. 發送一筆正常請求確認功能正常

**測試動作**:
1. 發送正常公司名稱（如「台積電」），觀察目前 aspect_summaries 的輸出
2. 觀察目前 generate_node 的 web_content 格式

**測試目標**: 確認 API 可正常運作，了解目前行為

**完成標準**:
- [ ] API server 可啟動
- [ ] 正常請求可返回內容
- [ ] 記錄目前 aspect_summaries 輸出格式

---

### Step 2: 實作 Task 1 - field → aspect mapping

**時機**: Step 1 完成後

**檔案**: `src/langgraph_state/company_brief_graph.py`

**變更內容**:
1. 新增 FIELD_TO_ASPECT mapping 配置
2. 修改 `summary_node()` 使用 field → aspect mapping
3. 不要填充空的 aspect（只輸出有的）

**程式碼範例**:

```python
# 新增：field → aspect mapping 配置
FIELD_TO_ASPECT = {
    "unified_number": "foundation",
    "capital": "foundation",
    "founded_date": "foundation",
    "address": "foundation",
    "officer": "vibe",
    "main_services": "core",
    "business_items": "core",
}

def summary_node(state: CompanyBriefState) -> CompanyBriefState:
    # ... existing code ...
    
    # 新增：使用 field → aspect mapping
    aspect_summaries = {}
    search_result = state.get("search_result")
    
    if search_result and search_result.results:
        for result in search_result.results:
            # 根據 field 映射到 aspect
            field = result.get("field")
            if field and field in FIELD_TO_ASPECT:
                aspect = FIELD_TO_ASPECT[field]
                # 只加入有值的內容
                if result.get("content"):
                    aspect_summaries[aspect] = AspectSummaryResult(
                        aspect=aspect,
                        description=aspect,  # 或從 mapping 取得 description
                        content=result["content"],
                        source_queries=[],
                        total_characters=len(result.get("content", "")),
                    )
    
    # ... existing code ...
```

**測試目標**: 
- 確認 field 能正確映射到 aspect
- 確認空的 aspect 不會被填充

**完成標準**:
- [ ] FIELD_TO_ASPECT 配置正確
- [ ] 搜尋結果能正確映射到 aspect
- [ ] 不會填充空的 aspect

---

### Step 3: 實作 Task 2 - format_content() 自動判斷

**時機**: Step 2 完成後

**檔案**: `src/functions/utils/prompt_builder.py` 或新檔案

**變更內容**:
1. 新增 `format_content()` function
2. 自動判斷資料格式（aspect 或 user_input）
3. 只輸出有值的內容

**程式碼範例**:

```python
def format_content(data):
    """
    自動判斷資料格式並格式化輸出
    
    Args:
        data: dict，aspect_summaries 或 user_input 格式
        
    Returns:
        str: 格式化後的字串
    """
    if not data:
        return ""
    
    # 判斷格式：aspect 格式有 foundation/core/vibe/future 鍵
    if any(key in data for key in ["foundation", "core", "vibe", "future"]):
        # aspect 格式
        parts = []
        for key in ["foundation", "core", "vibe", "future"]:
            value = data.get(key)
            if value:
                if hasattr(value, "content"):
                    content = value.content
                else:
                    content = str(value)
                parts.append(f"【{key}】\n{content}")
        return "\n\n".join(parts)
    else:
        # user_input 格式
        parts = []
        for key, value in data.items():
            if value:
                parts.append(f"{key}：{value}")
        return "\n".join(parts)
```

**測試目標**:
- 確認 aspect 格式能正確輸出
- 確認 user_input 格式能正確輸出
- 確認只輸出有值的內容

**完成標準**:
- [ ] format_content() 能正確判斷 aspect 格式
- [ ] format_content() 能正確判斷 user_input 格式
- [ ] 不會輸出空值

---

### Step 4: 實作 Task 3 - generate_node 降級邏輯

**時機**: Step 3 完成後

**檔案**: `src/langgraph_state/company_brief_graph.py`

**變更內容**:
1. 修改 `generate_node()` 的 web_content 取得邏輯
2. 當 aspect_summaries 為空時，使用 user_input 生成
3. 使用 format_content() 格式化內容

**程式碼範例**:

```python
def generate_node(state: CompanyBriefState) -> CompanyBriefState:
    # ... existing code ...
    
    # 新增：降級邏輯
    web_content = None
    aspect_summaries = state.get("aspect_summaries")
    user_input = state.get("user_brief")
    
    if aspect_summaries and any(aspect_summaries.values()):
        # 有 aspect_summaries，使用 aspect 格式
        from src.functions.utils.prompt_builder import format_content
        web_content = format_content(aspect_summaries)
        logger.info(f"使用 aspect_summaries 生成簡介")
    elif user_input:
        # aspect_summaries 為空，使用 user_input
        web_content = user_input
        logger.info(f"aspect_summaries 為空，使用 user_input 生成簡介")
    else:
        # 兩者都沒有，無法生成
        raise Exception("無法生成簡介：無搜尋結果且無用戶素材")
    
    # ... existing code ...
```

**測試目標**:
- 確認有 aspect_summaries 時使用 aspect 格式
- 確認 aspect_summaries 為空時使用 user_input
- 確認兩者都沒有時會報錯

**完成標準**:
- [ ] 有 aspect_summaries 時使用 aspect 格式
- [ ] aspect_summaries 為空時使用 user_input
- [ ] 兩者都沒有時拋出例外

---

### Step 5: 整合測試

**時機**: 所有 Task 完成後

**測試動作**:
1. 測試案例 A：有搜尋結果 → 應使用 aspect_summaries
2. 測試案例 B：無搜尋結果但有 user_input → 應使用 user_input
3. 測試案例 C：無搜尋結果且無 user_input → 應報錯

**測試目標**: 所有降級情境都能正確處理

**完成標準**:
- [ ] 測試案例 A 通過
- [ ] 測試案例 B 通過
- [ ] 測試案例 C 通過

---

## 3. 測試目標與標準

### 3.1 功能測試

| 項目 | 測試目標 | 預期結果 |
|------|---------|---------|
| field mapping | field 能正確映射到 aspect | 搜尋結果的 field 欄位對應到正確的 aspect |
| format_content aspect | aspect 格式能正確輸出 | 輸出格式為「【foundation】\n...」 |
| format_content user_input | user_input 格式能正確輸出 | 輸出格式為「key：value」 |
| 降級邏輯 | aspect_summaries 為空時使用 user_input | web_content = user_input |
| 空值處理 | 不會輸出空值 | 只有有值的內容會被輸出 |

### 3.2 測試案例

#### Test Case 1: 有搜尋結果

**輸入**:
- organ: "台積電"
- search_result: 有多個 aspect 結果

**預期輸出**:
- 使用 aspect_summaries 生成
- 格式為「【foundation】\n...」

#### Test Case 2: 無搜尋結果但有 user_input

**輸入**:
- organ: "不存在的公司"
- search_result: 空或失敗
- user_brief: "這是一間新創公司，專注於 AI 領域"

**預期輸出**:
- 使用 user_input 生成
- 格式為「這是一間新創公司...」

#### Test Case 3: 無搜尋結果且無 user_input

**輸入**:
- organ: "不存在的公司"
- search_result: 空或失敗
- user_brief: None

**預期輸出**:
- 拋出例外
- 錯誤訊息：「無法生成簡介：無搜尋結果且無用戶素材」

---

## 4. 完成後要紀錄與更新的文件

### 4.1 需更新的文件

| 文件 | 更新內容 |
|------|---------|
| `docs/agent_context/phase21/DEVELOPMENT_PLAN.md` | 新增 1.2.0 版本記錄，標記為完成 |
| `docs/agent_context/phase21/README.md` | 更新狀態與版本歷史 |
| `README.md` | （可選）更新功能說明 |

### 4.2 需紀錄的內容

- 測試截圖/日誌
- 實際程式碼變更
- 測試結果

---

## 5. 任務邊界與禁止事項

### 5.1 開發邊界（負責範圍）

| 元件 | 開發者職責 |
|------|-----------|
| `company_brief_graph.py` | summary_node + generate_node 修改 |
| `prompt_builder.py` | format_content() 新增 |
| FIELD_TO_ASPECT | mapping 配置 |

### 5.2 禁止事項

| 項目 | 禁止原因 |
|------|---------|
| **修改現有的錯誤處理邏輯** | 維持 Phase 21 的錯誤傳遞機制 |
| **修改 Phase 20 的錯誤代碼** | 避免破壞現有定義 |
| **修改 API 端點 URL** | 只修改內部邏輯，不改變 API 介面 |
| **填充空的 aspect** | 不要輸出空的內容 |
| **刪除現有功能** | 維持向後兼容 |

### 5.3 外部依賴（不在本次開發範圍）

| 項目 | 說明 |
|------|------|
| LLM API | 不需修改 |
| 搜尋工具 | 不需修改 |
| 前端 | 不需修改 |
| 其他 API | 不需修改 |

---

## 6. 風險與對應

| 風險 | 影響 | 對應方式 |
|------|------|---------|
| field mapping 漏掉某些 field | 某些資訊無法正確映射 | 先確認所有可能的 field 類型 |
| format_content 判斷錯誤 | 生成內容格式不正確 | 增加單元測試驗證 |
| 降級邏輯判斷錯誤 | 該用 user_input 時沒用到 | 增加整合測試驗證 |
| 429 錯誤頻繁觸發 | 測試無法進行 | 使用單次請求測試，間隔 30 秒 |

---

## 7. 進度追蹤

| 步驟 | 狀態 | 開始日期 | 結束日期 | 備註 |
|------|------|----------|----------|------|
| Step 1 | ✅ 完成 | 2026-04-23 | 2026-04-23 | API 在 port 5000，確認目前行為 |
| Step 2 | ✅ 完成 | 2026-04-23 | 2026-04-23 | 使用現有 CONFIG_DRIVEN_ENABLED |
| Step 3 | ✅ 完成 | 2026-04-23 | 2026-04-23 | 新增 format_content() |
| Step 4 | ✅ 完成 | 2026-04-23 | 2026-04-23 | 降級邏輯已實作 |
| Step 5 | ✅ 完成 | 2026-04-23 | 2026-04-23 | 測試通過 |
| Step 6 | ✅ 完成 | 2026-04-23 | 2026-04-23 | 統一 user_input 為 dict |
| 搜尋超時測試 | ✅ 完成 | 2026-04-23 | 2026-04-23 | Mock TimeoutError → SVC_002 映射正確 |
| SVC_001/003/004 測試 | ✅ 完成 | 2026-04-23 | 2026-04-23 | SVC_004 已實作，SVC_001/003 為預設或未觸發 |
| LLM 429 測試 | ⚠️ 待測試 | - | - | API 配額充足，未能觸發 |

---

## 8. 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 0.3.0 | 2026-04-23 | 初始規劃：降級機制與 format_content() |
| 0.3.1 | 2026-04-23 | 完成實作：統一 user_input 為 dict 格式，規格化 input 流程 |
| 0.3.2 | 2026-04-23 | 修正：ValidationError log level 改為 INFO，移除"驗證錯誤" prefix |
| 0.3.3 | 2026-04-23 | 完成：錯誤處理整合測試通過 8 個測試案例 |
| 0.3.4 | 2026-04-23 | 完成：搜尋超時測試（Mock TimeoutError → SVC_002 映射正確） |
| 0.3.5 | 2026-04-23 | 完成：SVC_001/003/004 錯誤處理驗證（SVC_004 已實作） |
| 0.3.6 | 2026-04-23 | 修正：錯誤代碼統一使用 ErrorCode 枚舉（company_brief_graph.py, llm_service.py） |
| 0.3.7 | 2026-04-23 | 修正：api_controller.py 使用 ErrorResponse schema 回傳錯誤 |
| 0.3.8 | 2026-04-23 | （預留：下次迭代） |

---

## 9. 開發 Prompt

請參考 `DEVELOPMENT_PROMPT_SUMMARY.md`