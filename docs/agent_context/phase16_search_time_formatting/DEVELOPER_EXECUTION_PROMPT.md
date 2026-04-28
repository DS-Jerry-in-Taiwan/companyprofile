# Phase 16 - Development Agent 執行 Prompt

**日期**: 2026-04-15
**階段**: Phase 16 搜尋時格式化優化
**執行模式**: 逐步驗證，每步完成後確認進度

---

## 📋 任務概述

你的任務是實現「搜尋時格式化」優化，將搜尋結果從純文字改為結構化 JSON，使 Summary Node 能正確合併並提升 Generate 的輸入品質。

**預計耗時**: 3-5 天
**預計工項**: 6 個
**參考文件**: `docs/agent_context/phase16_search_time_formatting/`

---

## 🎯 工項總覽

| # | 工項 | 檔案 | 狀態 | 目標 |
|---|------|------|------|------|
| 1 | 設計搜尋 Prompt 結構化格式 | `design_spec.md` | ⏳ 進行中 | 定義 JSON schema |
| 2 | 更新 `GeminiFewShotSearchTool` | `search_tools.py` | ⏸️ 待開始 | 返回四面向 JSON |
| 3 | 更新 `GeminiPlannerTavilyTool` | `search_tools.py` | ⏸️ 待開始 | 規劃四面向查詢 |
| 4 | 更新 `summary_node` 合併邏輯 | `company_brief_graph.py` | ⏸️ 待開始 | 合併結構化資料 |
| 5 | 測試驗證 | `tests/test_search_formatting.py` | ⏸️ 待開始 | 100% 通過驗收 |
| 6 | 文件更新 | context 文件 | ⏸️ 待開始 | 完成交付記錄 |

---

## 📖 關鍵文件位置

**規劃文件**（已準備好）:
- `docs/agent_context/phase16_search_time_formatting/01_dev_goal_context.md` - 階段目標、邊界、工項
- `docs/agent_context/phase16_search_time_formatting/02_dev_flow_context.md` - 詳細流程、驗收步驟
- `docs/agent_context/phase16_search_time_formatting/04_agent_prompts_context.md` - 逐步提示詞

**代碼文件**（需修改）:
- `src/services/search_tools.py` - 搜尋 Prompt 優化
- `src/langgraph_state/company_brief_graph.py` - Summary Node 更新
- `tests/test_search_formatting.py` - 新建測試檔案

---

## 🚀 執行流程（6 步走）

### ✅ Step 1: 設計搜尋 Prompt 結構化格式（0.5 天）

**目標**: 定義清晰的 JSON schema，使搜尋 LLM 能準確輸出

**任務清單**:
1. [ ] 建立 `docs/agent_context/phase16_search_time_formatting/design_spec.md`
2. [ ] 定義四個面向的 JSON 結構和內容要求
3. [ ] 提供具體例子（每個面向）
4. [ ] 定義長度限制和去重要求

**輸出範本**:
```markdown
# 搜尋結果結構化格式設計

## JSON Schema

### foundation（品牌實力與基本資料）
- 內容包括：成立時間、資本額、統一編號、公司地址等
- 最大長度：500 字
- 範例：「Google LLC 成立於 1998 年...」

### core（技術產品與服務核心）
- 內容包括：主營業務、技術亮點、產品特徵等
- 最大長度：500 字
- 範例：「Google 主要提供搜尋、廣告...」

### vibe（職場環境與企業文化）
- 內容包括：員工評價、企業文化、工作環境等
- 最大長度：500 字
- 範例：「Google 以開放創新的企業文化著稱...」

### future（近期動態與未來展望）
- 內容包括：近期新聞、發展方向、融資情況等
- 最大長度：500 字
- 範例：「Google 正在投資 AI 和量子計算...」

## Prompt 要求

在搜尋 LLM 的 prompt 中加入：
1. 四個面向的明確定義
2. JSON 格式要求
3. 字數限制和去重要求
```

**驗收標準**:
- [ ] `design_spec.md` 存在且內容完整
- [ ] 四個面向定義清晰無歧義
- [ ] 提供了具體例子
- [ ] JSON 結構明確

**完成信號**: 文件建立完成，回報進度

---

### ⏳ Step 2: 更新 `GeminiFewShotSearchTool` Prompt（1 天）

**目標**: 修改 Gemini Few-shot 搜尋工具的 prompt，要求返回四面向 JSON

**檔案**: `src/services/search_tools.py` 第 187-250 行

**任務清單**:
1. [ ] 找到 `GeminiFewShotSearchTool` 類別
2. [ ] 找到 `GEMINI_PROMPT_TEMPLATE` 字符串
3. [ ] 修改「輸出格式」部分，改為四面向 JSON 結構
4. [ ] 加入「去重」和「長度控制」要求

**修改範例**:

**修改前**:
```python
GEMINI_PROMPT_TEMPLATE = """你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{
    "company_name": "公司名稱",
    "unified_number": "統一編號（8位數字）",
    ...
}
"""
```

**修改後**:
```python
GEMINI_PROMPT_TEMPLATE = """你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{
    "foundation": "品牌實力與基本資料（不超過 500 字）...",
    "core": "技術產品與服務核心（不超過 500 字）...",
    "vibe": "職場環境與企業文化（不超過 500 字）...",
    "future": "近期動態與未來展望（不超過 500 字）..."
}

【特別要求】
1. 每個面向控制在 500 字以內，去除冗餘
2. 去除重複資訊，合併相同內容
3. 優先使用最新和最準確的資訊
4. 如果找不到某面向的資訊，返回「暫無相關資訊」
"""
```

**驗證步驟**:
```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.search_tools import create_search_tool
tool = create_search_tool('gemini_fewshot')
result = tool.search('Google')
print(f'Success: {result.success}')
print(f'Data keys: {list(result.data.keys())}')
# 應該看到 foundation, core, vibe, future 或 raw
assert result.success, 'Search failed'
assert any(k in result.data for k in ['foundation', 'core', 'vibe', 'future', 'raw']), 'Missing expected keys'
print('✅ 工項 2 驗證通過')
"
```

**驗收標準**:
- [ ] Prompt 修改完成
- [ ] 搜尋能返回 JSON（可能是 raw 格式如果 parse 失敗）
- [ ] 無 API 錯誤
- [ ] 結果包含預期欄位

**完成信號**: 驗證通過，回報結果

---

### ⏳ Step 3: 更新 `GeminiPlannerTavilyTool` Prompt（1 天）

**目標**: 修改 Gemini 規劃 + Tavily 執行工具，使其規劃四面向查詢

**檔案**: `src/services/search_tools.py` 第 337-408 行

**任務清單**:
1. [ ] 找到 `GeminiPlannerTavilyTool` 類別
2. [ ] 找到 `GEMINI_PLANNER_PROMPT` 字符串
3. [ ] 修改「欄位定義」部分，改為四個面向
4. [ ] 修改查詢構建邏輯，確保 Tavily 結果按面向組織
5. [ ] 修改結果合併邏輯，按面向合併

**修改範例**:

**修改前（欄位定義）**:
```python
GEMINI_PLANNER_PROMPT = """...
【欄位定義】
- unified_number: 統一編號（8位數）
- capital: 資本額
- founded_date: 成立時間
...
"""
```

**修改後（欄位定義）**:
```python
GEMINI_PLANNER_PROMPT = """...
【面向定義】
- foundation: 品牌實力與基本資料
- core: 技術產品與服務核心
- vibe: 職場環境與企業文化
- future: 近期動態與未來展望

【查詢規則】
1. 根據公司名稱，規劃最適合的搜尋關鍵字
2. 每個面向規劃 2-3 個查詢
3. 優先查最重要的資訊
4. 每個查詢要具體明確
"""
```

**修改結果合併邏輯**:

**修改前**:
```python
merged[field] = answer[:100] if len(answer) > 100 else answer
```

**修改後**:
```python
# 按面向合併多個查詢結果
if field in merged:
    merged[field] += "\n" + answer  # 相同面向追加
else:
    merged[field] = answer
```

**驗證步驟**:
```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.search_tools import create_search_tool
tool = create_search_tool('gemini_planner_tavily')
result = tool.search('Apple')
print(f'Success: {result.success}')
print(f'API calls: {result.api_calls}')
print(f'Data structure: {type(result.data).__name__}')
print(f'Data keys: {list(result.data.keys()) if isinstance(result.data, dict) else \"raw\"}')
assert result.success, 'Search failed'
assert result.api_calls > 1, 'API calls should be > 1'
print('✅ 工項 3 驗證通過')
"
```

**驗收標準**:
- [ ] Prompt 修改完成
- [ ] 規劃包含四個面向查詢
- [ ] Tavily API 調用成功（api_calls > 1）
- [ ] 結果能正確合併
- [ ] 無 API 錯誤

**完成信號**: 驗證通過，回報結果

---

### ⏳ Step 4: 更新 `summary_node` 合併邏輯（1 天）

**目標**: 改為合併結構化資料而非純文字

**檔案**: `src/langgraph_state/company_brief_graph.py` 第 167-250 行

**任務清單**:
1. [ ] 在 `summary_node` 前新增檢測函數
2. [ ] 實現 `is_structured_format()` - 檢查搜尋結果是否已結構化
3. [ ] 實現 `merge_structured_results()` - 合併結構化資料
4. [ ] 實現 `merge_plain_text_results()` - Fallback 到舊邏輯
5. [ ] 在 `summary_node` 中使用新邏輯

**程式碼範例**:

```python
def is_structured_format(search_result):
    """檢查搜尋結果是否已經是結構化格式"""
    if not search_result or not search_result.results:
        return False
    
    aspects = set()
    for result in search_result.results:
        if isinstance(result, dict) and 'aspect' in result:
            aspects.add(result['aspect'])
    
    # 至少有 2 個面向認為是結構化格式
    return len(aspects) >= 2


def merge_structured_results(search_result):
    """合併結構化搜尋結果為四面向摘要"""
    aspect_summaries = {}
    
    for aspect in ["foundation", "core", "vibe", "future"]:
        aspect_results = [
            r for r in search_result.results 
            if isinstance(r, dict) and r.get("aspect") == aspect
        ]
        
        if aspect_results:
            # 合併同面向的多個結果
            combined_parts = []
            for r in aspect_results:
                content = r.get("content") or r.get("answer", "")
                if content and content.strip():
                    combined_parts.append(content.strip())
            
            combined_content = "\n\n".join(combined_parts)
            
            aspect_summaries[aspect] = AspectSummaryResult(
                aspect=aspect,
                description=FourAspectSummarizer.ASPECT_DESCRIPTIONS[aspect],
                content=combined_content,
                source_queries=len(aspect_results),
                total_characters=len(combined_content),
            )
    
    return aspect_summaries


# 在 summary_node 中使用
if is_structured_format(search_result):
    # 新邏輯：合併結構化資料
    aspect_summaries = merge_structured_results(search_result)
else:
    # 舊邏輯：使用現有的 FourAspectSummarizer
    summarizer = FourAspectSummarizer()
    summaries = summarizer.summarize(...)
    # ... (保留現有邏輯)
```

**驗證步驟**:
```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.langgraph_state.company_brief_graph import summary_node
from src.services.search_tools import SearchResult

# 測試結構化輸入
search_result = SearchResult(
    success=True,
    results=[
        {'aspect': 'foundation', 'content': '公司成立於2010年', 'success': True},
        {'aspect': 'foundation', 'content': '資本額5000萬', 'success': True},
        {'aspect': 'core', 'content': '主營科技業務', 'success': True},
    ]
)
state = {
    'organ': '測試公司',
    'search_result': search_result,
    'execution_path': [],
    'current_node': None,
    'retry_counts': {},
}
result_state = summary_node(state)
assert 'aspect_summaries' in result_state, 'Missing aspect_summaries'
assert result_state['aspect_summaries'] is not None, 'aspect_summaries is None'
print(f'Aspect summaries: {list(result_state[\"aspect_summaries\"].keys())}')
print('✅ 工項 4 驗證通過')
"
```

**驗收標準**:
- [ ] 檢測函數實現正確
- [ ] 結構化合併邏輯工作正常
- [ ] Fallback 機制完善
- [ ] 輸出格式不變（仍是 `aspect_summaries`）
- [ ] 無回歸問題

**完成信號**: 驗證通過，回報結果

---

### ⏳ Step 5: 測試驗證（1 天）

**目標**: 確認全流程正常工作，達成所有驗收標準

**任務清單**:
1. [ ] 建立 `tests/test_search_formatting.py`
2. [ ] 實現搜尋格式檢驗測試
3. [ ] 實現 summary_node 測試
4. [ ] 實現端到端流程測試
5. [ ] 執行所有測試，確認 100% 通過

**測試代碼框架**:

```python
# tests/test_search_formatting.py

import pytest
from src.services.search_tools import create_search_tool
from src.langgraph_state.company_brief_graph import summary_node
from src.services.search_tools import SearchResult


class TestSearchFormatting:
    """搜尋格式化測試"""
    
    def test_gemini_fewshot_returns_structured_format(self):
        """驗證 gemini_fewshot 返回結構化格式"""
        tool = create_search_tool('gemini_fewshot')
        result = tool.search('Google')
        assert result.success
        # 檢查是否包含預期的面向
        assert any(k in result.data for k in ['foundation', 'core', 'vibe', 'future', 'raw'])
        print('✅ gemini_fewshot 返回結構化格式')
    
    def test_gemini_planner_tavily_returns_structured_format(self):
        """驗證 gemini_planner_tavily 返回結構化格式"""
        tool = create_search_tool('gemini_planner_tavily')
        result = tool.search('Apple')
        assert result.success
        assert result.api_calls > 1
        print('✅ gemini_planner_tavily 返回結構化格式')
    
    def test_summary_node_merges_structured_results(self):
        """驗證 summary_node 能正確合併結構化資料"""
        search_result = SearchResult(
            success=True,
            results=[
                {'aspect': 'foundation', 'content': '成立於2015年', 'success': True},
                {'aspect': 'foundation', 'content': '資本額5000萬', 'success': True},
            ]
        )
        state = {
            'organ': '測試公司',
            'search_result': search_result,
            'execution_path': [],
            'current_node': None,
            'retry_counts': {},
        }
        result_state = summary_node(state)
        assert 'aspect_summaries' in result_state
        assert result_state['aspect_summaries'] is not None
        print('✅ summary_node 正確合併')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**驗證步驟**:
```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -m pytest tests/test_search_formatting.py -v
```

**預期輸出**:
```
test_gemini_fewshot_returns_structured_format PASSED
test_gemini_planner_tavily_returns_structured_format PASSED
test_summary_node_merges_structured_results PASSED

===== 3 passed in X.XXs =====
```

**驗收標準**:
- [ ] 所有測試 100% 通過
- [ ] 搜尋結果格式正確
- [ ] Summary node 合併正確
- [ ] 無 API 錯誤
- [ ] 無 timeout

**完成信號**: 測試全部通過，回報結果

---

### ⏳ Step 6: 文件更新（0.5 天）

**目標**: 完整記錄 Phase 16 的實作、測試和交付

**任務清單**:
1. [ ] 更新 `05_validation_checklist.md` - 填入驗收結果
2. [ ] 更新 `06_delivery_record.md` - 記錄交付情況
3. [ ] 更新進度追蹤表

**驗收標準**:
- [ ] `design_spec.md` 完整
- [ ] 驗收清單全部勾選
- [ ] 交付記錄簽核完成
- [ ] 所有工項標記為完成

**完成信號**: 文件更新完成，提供完整摘要

---

## 📊 進度追蹤

完成每個工項後，請按以下格式回報：

```
✅ 工項 X 完成

【修改內容】
- 檔案：xxx.py
- 行數：XXX-XXX
- 修改說明：...

【驗證結果】
- 測試命令：...
- 預期結果：...
- 實際結果：✅ 通過 / ❌ 失敗

【問題（如有）】
- 問題：...
- 解決方案：...

準備開始工項 X+1
```

---

## 🆘 遇到問題時

1. **搜尋 API 失敗**
   - 檢查 GEMINI_API_KEY 和 TAVILY_API_KEY
   - 確認 prompt 語法正確（特別是 JSON 格式）

2. **JSON Parse 失敗**
   - 實作 fallback 邏輯（改回純文字）
   - 調整 prompt 以提高 JSON 格式正確率

3. **測試失敗**
   - 檢查程式邏輯是否符合預期
   - 驗證搜尋結果格式是否正確
   - 查看詳細錯誤信息

4. **無法決策**
   - 參考 `02_dev_flow_context.md` 的驗收步驟
   - 查看 `04_agent_prompts_context.md` 的示例
   - 向 Architect 報告

---

## ✅ 成功標準總結

**完成此 Phase 16 的條件**:

- [ ] 所有 6 個工項完成
- [ ] 所有驗收清單項目通過（✅）
- [ ] 測試 100% 通過
- [ ] 文件全部更新
- [ ] 無回歸問題
- [ ] 交付記錄簽核完成

---

## 🎯 開始執行

**現在開始 Step 1：設計搜尋 Prompt 結構化格式**

請建立 `design_spec.md`，內容包括：
1. 四個面向的定義和例子
2. JSON 結構說明
3. 長度限制和去重要求
4. Prompt 要求

完成後回報，我會審核並指導進入 Step 2。
