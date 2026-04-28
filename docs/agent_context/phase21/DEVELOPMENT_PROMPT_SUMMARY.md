# Phase 21 附錄：Summary 流程調整 - 開發指令

**執行者**: Development Agent  
**參考文件**: `docs/agent_context/phase21/DEVELOPMENT_PLAN_SUMMARY.md`

---

## 任務目標

實作降級機制與 format_content()，確保：
1. 搜尋結果能正確映射到 aspect（field → aspect mapping）
2. 當 aspect_summaries 為空時，能使用 user_input 生成簡介
3. prompt builder 能自動判斷內容格式，只給有值的內容

---

## 設計架構

```
search_node → summary_node (field → aspect mapping) → 
generate_node (用 aspect_summaries 或 user_input 生成) →
quality_check_node → END
```

### 降級邏輯

| 情況 | aspect_summaries | user_input | 行為 |
|------|-------------------|------------|------|
| 有搜尋結果 | ✅ 有（部分或全部） | 有/無 | 用 aspect_summaries 生成 |
| 無搜尋結果 | ❌ 空 | ✅ 有 | 用 user_input 生成 |
| 無搜尋結果 + 無 user_input | ❌ 空 | ❌ 無 | 報錯 |

---

## 執行步驟

### Step 1: 環境準備與現狀確認

1. 確認所有相關程式碼在本地可用
2. 啟動 API server (`python scripts/test_api_server.py`)
3. 發送一筆正常請求確認功能正常
4. 觀察目前 aspect_summaries 的輸出格式
5. 觀察目前 generate_node 的 web_content 格式

**完成標準**:
- [ ] API server 可啟動
- [ ] 正常請求可返回內容
- [ ] 記錄目前 aspect_summaries 輸出格式

---

### Step 2: 實作 Task 1 - field → aspect mapping

**檔案**: `src/langgraph_state/company_brief_graph.py`

**變更內容**:
1. 在檔案頂部（或 summary_node 附近）新增 FIELD_TO_ASPECT mapping 配置
2. 修改 `summary_node()` 使用 field → aspect mapping
3. 不要填充空的 aspect

**程式碼範例**:

```python
# 新增：field → aspect mapping 配置（放在 import 區塊附近）
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

**變更 summary_node 的邏輯**:
- 取得搜尋結果的 field 欄位
- 根據 FIELD_TO_ASPECT 映射到 aspect
- 只加入有值的內容，不要填充空的 aspect

**測試目標**: 
- 確認 field 能正確映射到 aspect
- 確認空的 aspect 不會被填充

**完成標準**:
- [ ] FIELD_TO_ASPECT 配置正確
- [ ] 搜尋結果能正確映射到 aspect
- [ ] 不會填充空的 aspect

---

### Step 3: 實作 Task 2 - format_content() 自動判斷

**檔案**: `src/functions/utils/prompt_builder.py`（在現有檔案新增 function）

**變更內容**:
1. 在檔案末尾新增 `format_content()` function
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

**檔案**: `src/langgraph_state/company_brief_graph.py`

**變更內容**:
1. 修改 `generate_node()` 的 web_content 取得邏輯
2. 當 aspect_summaries 為空時，使用 user_input 生成
3. 使用 format_content() 格式化內容

**程式碼範例**:

```python
def generate_node(state: CompanyBriefState) -> CompanyBriefState:
    # ... existing code (imports, logging, start_time) ...
    
    # 新增：降級邏輯
    web_content = None
    aspect_summaries = state.get("aspect_summaries")
    user_input = state.get("user_brief")
    
    # 檢查 aspect_summaries 是否有內容
    has_aspect_content = False
    if aspect_summaries:
        for key in ["foundation", "core", "vibe", "future"]:
            value = aspect_summaries.get(key)
            if value and (hasattr(value, "content") and value.content):
                has_aspect_content = True
                break
    
    if has_aspect_content:
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
    
    # ... existing code (prompt building, LLM call, etc.) ...
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

**測試動作**:

1. **測試案例 A：有搜尋結果**
   ```bash
   curl -X POST http://localhost:5000/api/generate_brief \
     -H "Content-Type: application/json" \
     -d '{"organ": "台積電"}'
   ```
   - 預期：使用 aspect_summaries 生成

2. **測試案例 B：無搜尋結果但有 user_input**
   - 需要構造一個搜尋失敗但有 user_input 的測試案例
   - 預期：使用 user_input 生成

3. **測試案例 C：無搜尋結果且無 user_input**
   - 需要構造一個搜尋失敗且無 user_input 的測試案例
   - 預期：返回 500 錯誤

**完成標準**:
- [ ] 測試案例 A 通過
- [ ] 測試案例 B 通過
- [ ] 測試案例 C 通過

---

## 禁止事項

| 項目 | 禁止原因 |
|------|---------|
| **修改現有的錯誤處理邏輯** | 維持 Phase 21 的錯誤傳遞機制 |
| **修改 Phase 20 的錯誤代碼** | 避免破壞現有定義 |
| **修改 API 端點 URL** | 只修改內部邏輯，不改變 API 介面 |
| **填充空的 aspect** | 不要輸出空的內容 |
| **刪除現有功能** | 維持向後兼容 |

---

## 完成後的動作

1. 更新 `docs/agent_context/phase21/DEVELOPMENT_PLAN_SUMMARY.md` 的進度追蹤表格
2. 在 `docs/agent_context/phase21/DEVELOPMENT_PLAN.md` 新增版本記錄（1.2.0）
3. 確認所有測試通過
4. 提交程式碼變更