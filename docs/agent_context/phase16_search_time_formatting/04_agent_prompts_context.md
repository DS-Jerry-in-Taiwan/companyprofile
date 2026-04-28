# Phase 16 - Agent 提示詞上下文

**最後更新**: 2026-04-15

## 給 Development Agent 的逐步提示詞

---

### 第一步（工項 1）：設計搜尋 Prompt 結構化格式

**目標**：定義清晰的搜尋結果 JSON schema

**任務**：
1. 建立 `docs/agent_context/phase16_search_time_formatting/design_spec.md`
2. 定義四個面向的 JSON 結構
3. 提供具體例子
4. 定義長度限制和內容要求

**輸出範例**：

```markdown
# 搜尋結果結構化格式設計

## JSON Schema

{
  "foundation": {
    "description": "品牌實力與基本資料",
    "includes": ["成立時間", "資本額", "統一編號", "公司地址"],
    "max_length": 500,
    "example": "Google LLC 成立於 1998 年，是全球領先的搜尋引擎公司..."
  },
  "core": {
    "description": "技術產品與服務核心",
    "includes": ["主營業務", "技術亮點", "產品特徵"],
    "max_length": 500,
    "example": "Google 主要提供搜尋、廣告、雲服務等..."
  },
  "vibe": {
    "description": "職場環境與企業文化",
    "includes": ["員工評價", "企業文化", "工作環境"],
    "max_length": 500,
    "example": "Google 以開放創新的企業文化著稱..."
  },
  "future": {
    "description": "近期動態與未來展望",
    "includes": ["近期新聞", "發展方向", "融資情況"],
    "max_length": 500,
    "example": "Google 正在投資 AI 和量子計算..."
  }
}
```

完成後提供確認，我會審核並給予下一步指令。

---

### 第二步（工項 2）：更新 `GeminiFewShotSearchTool` Prompt

**目標**：修改搜尋 prompt，要求返回結構化 JSON

**檔案**：`src/services/search_tools.py` 第 187-250 行

**任務**：
1. 找到 `GEMINI_PROMPT_TEMPLATE`
2. 在「輸出格式」部分加入四面向的 JSON 結構
3. 加入「去重」和「長度控制」要求

**修改前**：
```python
GEMINI_PROMPT_TEMPLATE = """...
【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "company_name": "公司名稱",
    "unified_number": "統一編號",
    ...
}}
"""
```

**修改後**：
```python
GEMINI_PROMPT_TEMPLATE = """...
【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "foundation": "品牌實力與基本資料（不超過 500 字）...",
    "core": "技術產品與服務核心（不超過 500 字）...",
    "vibe": "職場環境與企業文化（不超過 500 字）...",
    "future": "近期動態與未來展望（不超過 500 字）..."
}}

【特別要求】
1. 每個面向控制在 500 字以內，去除冗餘
2. 去除重複資訊，合併相同內容
3. 優先使用最新和最準確的資訊
4. 如果找不到某面向的資訊，返回「暫無相關資訊」
"""
```

**驗證測試**：
```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.search_tools import create_search_tool
tool = create_search_tool('gemini_fewshot')
result = tool.search('Google')
print(f'Success: {result.success}')
print(f'Data: {result.data}')
# 應該看到 foundation, core, vibe, future 或 raw
assert result.success
print('✅ 工項 2 驗證通過')
"
```

驗證通過後提供結果，我會給予下一步指令。

---

### 第三步（工項 3）：更新 `GeminiPlannerTavilyTool` Prompt

**目標**：修改規劃 prompt，使 Gemini 規劃出四面向的查詢

**檔案**：`src/services/search_tools.py` 第 337-408 行

**任務**：
1. 找到 `GEMINI_PLANNER_PROMPT`
2. 在欄位定義部分改為四面向
3. 修改查詢構建邏輯，使 Tavily 結果按面向組織

**修改 Prompt**：
```python
GEMINI_PLANNER_PROMPT = """...
【欄位定義】
- foundation: 品牌實力與基本資料
- core: 技術產品與服務核心
- vibe: 職場環境與企業文化
- future: 近期動態與未來展望

【規則】
1. 根據公司名稱，規劃最適合的搜尋關鍵字
2. 每個面向規劃 2-3 個查詢
3. 優先查最重要的資訊
4. 每個查詢要具體明確
"""
```

**驗證測試**：
```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.search_tools import create_search_tool
tool = create_search_tool('gemini_planner_tavily')
result = tool.search('Apple')
print(f'Success: {result.success}')
print(f'API calls: {result.api_calls}')
print(f'Data keys: {list(result.data.keys()) if isinstance(result.data, dict) else \"raw\"}')
assert result.success
print('✅ 工項 3 驗證通過')
"
```

驗證通過後提供結果，我會給予下一步指令。

---

### 第四步（工項 4）：更新 `summary_node` 合併邏輯

**目標**：改為合併結構化資料而非純文字

**檔案**：`src/langgraph_state/company_brief_graph.py` 第 167-250 行

**任務**：
1. 檢測搜尋結果是否已經是結構化格式（包含 foundation/core/vibe/future）
2. 如果是結構化，直接使用；如果不是，兼容舊格式
3. 合併邏輯改為按面向組織

**修改邏輯**：

```python
def is_structured_format(search_result):
    """檢查搜尋結果是否已經是結構化格式"""
    if not search_result.results:
        return False
    # 檢查是否有 foundation/core/vibe/future
    aspects = set()
    for result in search_result.results:
        if 'aspect' in result:
            aspects.add(result['aspect'])
    return len(aspects) >= 2  # 至少有 2 個面向

# 在 summary_node 中
if is_structured_format(search_result):
    # 新邏輯：按面向合併
    for aspect in ["foundation", "core", "vibe", "future"]:
        aspect_results = [r for r in search_result.results if r.get("aspect") == aspect]
        if aspect_results:
            # 合併同面向的多個結果
            combined = "\n\n".join([r["content"] or r["answer"] for r in aspect_results])
            aspect_summaries[aspect] = AspectSummaryResult(aspect=aspect, content=combined, ...)
else:
    # 舊邏輯：兼容
    # 保留現有的純文字分發邏輯
```

**驗證測試**：
```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.langgraph_state.company_brief_graph import summary_node
from src.services.search_tools import SearchResult

# 模擬結構化搜尋結果
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
assert 'aspect_summaries' in result_state
assert result_state['aspect_summaries'] is not None
print('✅ 工項 4 驗證通過')
"
```

驗證通過後提供結果，我會給予下一步指令。

---

### 第五步（工項 5）：測試驗證

**目標**：確認全流程正常工作

**任務**：
1. 建立 `tests/test_search_formatting.py`
2. 測試搜尋結果格式
3. 測試 summary_node 合併
4. 端到端流程測試

**測試內容**：
```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -m pytest tests/test_search_formatting.py -v
```

應該看到：
```
test_gemini_fewshot_returns_structured_format PASSED
test_gemini_planner_tavily_returns_structured_format PASSED
test_summary_node_merges_structured_results PASSED
test_end_to_end_flow PASSED
```

提供驗證結果，我會給予下一步指令。

---

### 第六步（工項 6）：文件更新

**目標**：完整記錄 Phase 16 的實作和測試結果

**任務**：
1. 建立 `04_agent_prompts_context.md` - 本文件
2. 建立 `05_validation_checklist.md` - 驗收清單
3. 建立 `06_delivery_record.md` - 交付記錄
4. 更新 `design_spec.md` - 最終設計文件

完成全部 6 個工項且最終驗證通過後，請提供完整摘要報告。
