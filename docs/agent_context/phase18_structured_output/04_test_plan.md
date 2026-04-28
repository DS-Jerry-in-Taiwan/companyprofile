# Phase 18：步驟 4 - 測試計畫

**日期**: 2026-04-17
**步驟**: 4
**狀態**: ✅ 完成

---

## 🎯 步驟目標

驗證 Structured Output 實作正確，確保與完整流程相容。

---

## 📋 測試任務

### 測試 4.1：單元測試 - 輸出格式

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python3 -c "
from src.services.search_tools import ParallelAspectSearchTool

tool = ParallelAspectSearchTool(timeout=30)

# 測試多家公司
companies = [
    '台積電',
    '澳霸有限公司',
    '南晃交通器材工業股份有限公司',
    '鴻海',
]

print('=== 測試輸出格式 ===')

for company in companies:
    result = tool.search(company)

    print(f'\n{company}:')
    print(f'  成功: {result.success}')
    print(f'  API 呼叫: {result.api_calls}')

    for aspect, content in result.data.items():
        print(f'  {aspect}: {type(content).__name__} ({len(content)} 字)')

        # 驗證
        assert isinstance(content, str), f'{aspect} 應該是 str'
        assert not content.startswith('{'), f'{aspect} 不應該是 dict 格式'

print('\n✅ 所有測試通過')
"
```

### 測試 4.2：整合測試 - summary_node

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python3 -c "
from src.langgraph_state.company_brief_graph import generate_company_brief

# 測試一家公司
result = generate_company_brief(
    organ='澳霸有限公司',
    organ_no='117164920',
    word_limit=200,
    optimization_mode='STANDARD'
)

print('標題:', result.get('title'))
print('內容長度:', len(result.get('body_html', '')))
print('錯誤:', result.get('errors'))

# 驗證
assert result.get('title'), '應該有標題'
assert len(result.get('body_html', '')) > 100, '內容應該超過100字'
assert not result.get('errors'), '不應該有錯誤'

print('\n✅ 整合測試通過')
"
```

### 測試 4.3：Checkpoint 1 完整測試

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python3 scripts/checkpoint1/test_phase17_complete_flow.py
```

**預期結果**：
- 8 家測試公司全部成功
- 無 `'dict' object has no attribute 'strip'` 錯誤
- 輸出內容豐富（> 100 字）

---

## 📊 效能測試

### 測試 4.4：時間對比

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python3 -c "
import time
from src.services.search_tools import ParallelAspectSearchTool

tool = ParallelAspectSearchTool(timeout=30)

companies = ['台積電', '鴻海', '聯發科']

total_time = 0
for company in companies:
    start = time.time()
    result = tool.search(company)
    elapsed = time.time() - start
    total_time += elapsed
    print(f'{company}: {elapsed:.2f}s')

avg_time = total_time / len(companies)
print(f'\n平均時間: {avg_time:.2f}s')

# 驗證
assert avg_time < 15, f'平均時間應該小於15s，實際 {avg_time:.2f}s'
print('✅ 效能測試通過')
"
```

---

## ✅ 通過標準

### 功能測試
- [x] 測試 4.1：單元測試通過
- [x] 測試 4.2：整合測試通過
- [x] 測試 4.3：Checkpoint 1 測試通過

### 效能測試
- [x] 測試 4.4：時間對比正常
- [x] 平均時間 < 15s

### 品質測試
- [x] 輸出內容豐富（> 100 字）
- [x] 無格式錯誤
- [x] 無 `dict` 巢狀結構

---

## 📊 測試結果

### 單元測試結果
```
7/7 測試通過 ✅

- test_gemini_fewshot_returns_structured_format PASSED
- test_gemini_planner_tavily_returns_structured_format PASSED
- test_summary_node_merges_structured_results PASSED
- test_tavily_search_basic PASSED
- test_create_search_tool_with_string PASSED
- test_list_available_tools PASSED
- test_structured_search_to_summary_flow PASSED
```

### API 整合測試結果
```
4/4 API 測試通過 ✅

【測試 1】澳霸有限公司 (basic 策略)
  ✅ HTTP 200
  ✅ API Success: True
  ✅ Summary Length: 103 字
  ✅ Response Time: 4.03s

【測試 2】台積電 (basic 策略)
  ✅ HTTP 200
  ✅ API Success: True
  ✅ Summary Length: 102 字
  ✅ Response Time: 7.06s

【測試 3】澳霸有限公司 (complete 策略)
  ✅ HTTP 200
  ✅ API Success: True
  ✅ Summary Length: 106 字
  ✅ Response Time: 3.69s

【測試 4】台積電 (complete 策略)
  ✅ HTTP 200
  ✅ API Success: True
  ✅ Summary Length: 102 字
  ✅ Response Time: 8.03s
```

### 輸出格式驗證
```
GeminiFewShotSearchTool (basic 策略):
  foundation: ✅ str (250 字)
  core: ✅ str (79 字)
  vibe: ✅ str (94 字)
  future: ✅ str (84 字)

ParallelAspectSearchTool (complete 策略):
  foundation: ✅ str (91 字)
  core: ✅ str (71 字)
  vibe: ✅ str (79 字)
  future: ✅ str (73 字)
```

---

## 📊 預計工時

| 任務 | 工時 | 實際 |
|------|------|------|
| 任務 4.1：單元測試 | 0.5h | 0.25h ✅ |
| 任務 4.2：整合測試 | 0.5h | 0.5h ✅ |
| 任務 4.3：Checkpoint 測試 | 1h | 0.25h ✅ |
| **總計** | **2h** | **1h** |

---

*步驟完成時間：2026-04-17 14:30*
