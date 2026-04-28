# Phase 16 - 開發流程上下文

**最後更新**: 2026-04-15

## 流程概述

本階段採用「設計驗證 → 開發 → 測試 → 文件」的四階段流程，確保搜尋時格式化的正確性。

**當前狀態**: 規劃完成，待開發

---

## 階段一：設計驗證（0.5 天）

### 任務：定義搜尋結果結構化格式

**目標**：設計清晰的 JSON schema，使搜尋 LLM 能準確理解和輸出

**輸出**：`design_spec.md` 包含

```json
{
  "foundation": "品牌實力與基本資料，包含成立時間、資本額、統一編號等",
  "core": "技術產品與服務核心，包含主營業務、技術亮點、產品特徵等",
  "vibe": "職場環境與企業文化，包含員工評價、企業文化、工作環境等",
  "future": "近期動態與未來展望，包含近期新聞、發展方向、融資情況等"
}
```

**驗證清單**：
- [ ] 四個面向定義明確，無歧義
- [ ] 每個面向有具體例子
- [ ] 長度限制合理（500-800 字）

**完成信號**：`design_spec.md` 完成並通過審核

---

## 階段二：搜尋 Prompt 優化（2 天）

### 任務 1：更新 `GeminiFewShotSearchTool`（1 天）

**檔案**：`src/services/search_tools.py` Line 187-250

**修改內容**：
```python
GEMINI_PROMPT_TEMPLATE = """你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "foundation": "品牌實力與基本資料...",
    "core": "技術產品與服務核心...",
    "vibe": "職場環境與企業文化...",
    "future": "近期動態與未來展望..."
}}

【特別要求】
1. 每個面向控制在 500 字以內
2. 去除冗餘，合併重複資訊
3. 優先使用最新資訊
4. 如果找不到某面向的資訊，返回「暫無相關資訊」
"""
```

**驗證步驟**：
```bash
python -c "
from src.services.search_tools import create_search_tool
tool = create_search_tool('gemini_fewshot')
result = tool.search('Google')
print(f'Success: {result.success}')
print(f'Data keys: {list(result.data.keys())}')
print(f'Expected: foundation, core, vibe, future')
assert 'foundation' in result.data or 'raw' in result.data
print('✅ 測試通過')
"
```

**驗收標準**：
- [ ] 搜尋返回 JSON，包含四個面向欄位
- [ ] 無 parse 錯誤
- [ ] 內容質量正常

---

### 任務 2：更新 `GeminiPlannerTavilyTool`（1 天）

**檔案**：`src/services/search_tools.py` Line 337-408

**修改內容**：
1. Gemini 規劃 prompt 加入結構化要求：
```python
GEMINI_PLANNER_PROMPT = """...
【輸出格式】
{{
    "queries": [
        {{
            "field": "foundation",  # 對應四個面向之一
            "query": "Google成立時間、資本額、統一編號",
            "priority": 1
        }}
    ]
}}
"""
```

2. Tavily 結果合併邏輯改為按面向組織：
```python
# 舊邏輯：每個欄位一個查詢
# 新邏輯：多個查詢結果合併到同一面向
merged[field] = "\n".join([search_results[field]["answer"] for field in group])
```

**驗證步驟**：
```bash
python -c "
from src.services.search_tools import create_search_tool
tool = create_search_tool('gemini_planner_tavily')
result = tool.search('Apple')
print(f'Success: {result.success}')
print(f'Data structure: {result.data}')
# 驗證是否有四面向或相關內容
print('✅ 測試通過')
"
```

**驗收標準**：
- [ ] 規劃 prompt 正確理解四面向
- [ ] Tavily 結果能正確按面向合併
- [ ] 無 API 錯誤

---

## 階段三：Summary Node 更新（1 天）

### 任務：改為合併結構化資料

**檔案**：`src/langgraph_state/company_brief_graph.py` Line 167-250

**現有邏輯**：
```python
# 純文字拼接
combined_content = "\n\n".join([q["answer"] for q in queries])
```

**新邏輯**：
```python
# 檢查搜尋結果是否已經是結構化
if is_structured_format(search_result):
    # 直接使用結構化資料
    aspect_summaries = merge_structured_results(search_result)
else:
    # Fallback：兼容舊格式
    aspect_summaries = merge_plain_text_results(search_result)
```

**驗收標準**：
- [ ] 能正確識別結構化格式
- [ ] 合併邏輯正確
- [ ] Fallback 機制正常

---

## 階段四：測試驗證（1 天）

### 測試 1：搜尋結果格式檢驗

**檔案**：`tests/test_search_formatting.py`

```python
def test_gemini_fewshot_returns_structured_format():
    """驗證 gemini_fewshot 返回結構化格式"""
    tool = create_search_tool('gemini_fewshot')
    result = tool.search('Microsoft')
    assert result.success
    assert 'foundation' in result.data or 'raw' in result.data
    print('✅ gemini_fewshot 格式正確')

def test_gemini_planner_tavily_returns_structured_format():
    """驗證 gemini_planner_tavily 返回結構化格式"""
    tool = create_search_tool('gemini_planner_tavily')
    result = tool.search('Amazon')
    assert result.success
    # 驗證結果包含預期欄位
    print('✅ gemini_planner_tavily 格式正確')

def test_summary_node_merges_structured_results():
    """驗證 summary_node 能正確合併結構化資料"""
    search_result = SearchResult(
        success=True,
        results=[
            {"aspect": "foundation", "content": "成立於2015年", "success": True},
            {"aspect": "foundation", "content": "資本額5000萬", "success": True},
        ]
    )
    state = {"search_result": search_result, "organ": "測試公司"}
    result_state = summary_node(state)
    assert result_state["aspect_summaries"] is not None
    print('✅ summary_node 合併正確')
```

### 測試 2：端到端流程測試

**驗收清單**：
- [ ] Search → Summary → Generate 完整流程正常
- [ ] 生成結果質量 ≥ Phase 15
- [ ] 無 token 溢出
- [ ] 無 timeout

---

## 驗收流程

### 1. 代碼審查
- [ ] 搜尋 prompt 語法正確
- [ ] JSON 解析邏輯完整
- [ ] Fallback 機制健全
- [ ] 無重複代碼

### 2. 功能驗收
- [ ] 所有搜尋 provider 都工作正常
- [ ] Summary node 正確合併
- [ ] Generate 輸入品質正常

### 3. 性能驗收
- [ ] 搜尋耗時增加 < 20%（因為 prompt 變長）
- [ ] Token 使用增加在預期內（~10-15%）

### 4. 文件驗收
- [ ] Phase 16 context 文件完整
- [ ] design_spec.md 清晰準確

---

## 回滾計劃

如果發現問題，可以快速回滾：
1. 搜尋 prompt 改回純文字要求
2. Summary node 改回純文字拼接
3. 不涉及 database 或 config 改動，風險低

---

## 日常流程

### 每日檢查
```bash
# 驗證搜尋格式
python tests/test_search_formatting.py

# 驗證完整流程
python tests/test_end_to_end.py
```

### 問題升級
- 搜尋失敗 → 檢查 prompt
- Parse 失敗 → 檢查 fallback
- 質量下降 → 微調 prompt
