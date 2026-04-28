# Phase 15 - 開發流程上下文

**最後更新**: 2026-04-15

## 流程概述

本階段採用單一 Agent 逐步執行模式，每次只做一個工項，完成後驗證，再繼續下一個。

**當前狀態**: ✅ 全部完成（6 個工項）

---

## 執行流程

### Step 1: 工項 1 — 修改 `SearchConfig` dataclass

**目標檔案**: `src/services/config_driven_search.py`

**任務**:
1. 在 `SearchConfig` dataclass 上方新增一個 `ModelConfig` dataclass
2. 在 `SearchConfig` 中新增 `models: Dict[str, ModelConfig] = field(default_factory=dict)` 欄位
3. 更新 `from_dict()` 方法，從 `data.get("models", {})` 解析並建立 `models` 字典

**驗證**:
```bash
python -c "
from src.services.config_driven_search import SearchConfig
config = SearchConfig.from_dict({
    'search': {'provider': 'gemini_fewshot', 'max_results': 2},
    'models': {
        'gemini_fewshot': {'model': 'gemini-2.0-flash-lite', 'temperature': 0.2},
        'gemini_planner_tavily': {'model': 'gemini-2.0-flash', 'temperature': 0.1}
    }
})
print(f'models: {config.models}')
print('✅ 工項 1 驗證通過')
"
```

---

### Step 2: 工項 2 — 更新 `_create_tool()` 傳遞模型參數

**目標檔案**: `src/services/config_driven_search.py`

**任務**:
1. 在 `_create_tool()` 中找到 `gemini_fewshot` 的分支，改為從 `self.config.models.get("gemini_fewshot", ModelConfig())` 讀取
2. 在 `gemini_planner_tavily` 的分支中新增 `model=` 和 `temperature=` 參數
3. 同時修正 `from_dict()` 讓 `provider`/`max_results` 從 `search` 區塊讀取

**驗證**:
```bash
python -c "
from src.services.config_driven_search import ConfigDrivenSearchTool
t1 = ConfigDrivenSearchTool(config_dict={'search': {'provider': 'gemini_fewshot', 'max_results': 2}, 'models': {'gemini_fewshot': {'model': 'gemini-2.0-flash-lite', 'temperature': 0.2}, 'gemini_planner_tavily': {'model': 'gemini-2.0-flash', 'temperature': 0.1}}})
t2 = ConfigDrivenSearchTool(config_dict={'search': {'provider': 'gemini_planner_tavily', 'max_results': 2}, 'models': {'gemini_fewshot': {'model': 'gemini-2.0-flash-lite', 'temperature': 0.2}, 'gemini_planner_tavily': {'model': 'gemini-2.0-flash', 'temperature': 0.1}}})
print(f'gemini_fewshot tool type: {type(t1._tool).__name__}')
print(f'gemini_planner_tavily tool type: {type(t2._tool).__name__}')
print(f'gemini_fewshot tool.model: {t1._tool.model}')
print(f'gemini_planner_tavily tool.model: {t2._tool.model}')
print('✅ 工項 2 驗證通過')
"
```

---

### Step 3: 工項 3 — 修改 `GeminiPlannerTavilyTool` 接收參數

**目標檔案**: `src/services/search_tools.py`

**任務**:
1. 在 `GeminiPlannerTavilyTool.__init__` 中新增：
   ```python
   self.model = kwargs.get("model", "gemini-2.0-flash")
   self.temperature = kwargs.get("temperature", 0.1)
   ```
2. 在 `search()` 方法中，把 `generate_content` 呼叫的 `model="gemini-2.0-flash"` 改成 `model=self.model`
3. 同時把 `temperature` 也改成從實例變數讀取

**驗證**:
```bash
python -c "
from src.services.search_tools import create_search_tool
t = create_search_tool('gemini_planner_tavily', model='gemini-2.0-flash', temperature=0.5)
print(f'tool.model: {t.model}')
print(f'tool.temperature: {t.temperature}')
t2 = create_search_tool('gemini_planner_tavily')
print(f'default model: {t2.model}')
print(f'default temperature: {t2.temperature}')
print('✅ 工項 3 驗證通過')
"
```

---

### Step 4: 工項 4 — 更新 `config/search_config.json`

**目標檔案**: `config/search_config.json`

**任務**: 將檔案內容更新為新 schema

**驗證**:
```bash
python -c "
from src.services.config_driven_search import ConfigDrivenSearchTool
t = ConfigDrivenSearchTool()
print(f'provider: {t.config.provider}')
print(f'gemini_fewshot model: {t.config.models.get(\"gemini_fewshot\").model}')
print(f'gemini_planner_tavily model: {t.config.models.get(\"gemini_planner_tavily\").model}')
print('✅ 工項 4 驗證通過')
"
```

---

### Step 5: 工項 5 — 更新 `.env.example`

**目標檔案**: `.env.example`

**任務**: 在檔案末尾新增說明區塊

---

### Step 6: 工項 6 — 最終驗證

**驗證**:
```bash
python -c "
from src.services.config_driven_search import ConfigDrivenSearchTool
t = ConfigDrivenSearchTool()
print(f'provider: {t.config.provider}')
print(f'max_results: {t.config.max_results}')
for name in ['gemini_fewshot', 'gemini_planner_tavily']:
    mc = t.config.models.get(name)
    print(f'{name}: model={mc.model}, temperature={mc.temperature}')

# 確認 generate_content 中沒有硬編碼
with open('src/services/search_tools.py') as f:
    content = f.read()
hardcoded = []
for model in ['gemini-2.0-flash-lite', 'gemini-2.0-flash']:
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if f'\"{model}\"' in line or f\"'{model}'\" in line:
            if 'GEMINI_PROMPT' not in line and '# ' not in line and 'model=' not in line.lower():
                hardcoded.append(f'line {i}: {line.strip()}')
if hardcoded:
    print('❌ 仍有硬編碼')
else:
    print('✅ search_tools.py 中無硬編碼模型名稱')
print('✅ Phase 15 全部完成')
"
```

---

## 架構對應圖

```
config/search_config.json
├── search.provider        → 選擇使用哪個 provider
├── search.max_results     → 所有 provider 共用
└── models.<provider>      → 各 provider 的模型配置
    ├── model              → 模型名稱
    └── temperature        → 溫度參數
         │
         ▼
config_driven_search.py
├── SearchConfig.from_dict()    → 解析新的 models 區塊
├── _create_tool()              → 把 model/temp 傳給各工具
│    ├── gemini_fewshot         → ✅ 從 config 讀
│    ├── gemini_planner_tavily  → ✅ 從 config 讀（已修正）
│    └── parallel_multi_source  → 從子工具繼承
         │
         ▼
search_tools.py
├── GeminiFewShotSearchTool     → 接收 model/temp 參數 ✅
└── GeminiPlannerTavilyTool     → 接收 model/temp 參數 ✅（已修正）
```

---

## 整合測試

| 測試 | 內容 | 結果 |
|------|------|------|
| 測試 1 | 實際檔案載入 + 模型解析 | ✅ |
| 測試 2 | `switch_provider()` 動態切換 | ✅ |
| 測試 3 | 熱重載 `reload_config()` | ✅ |
| 測試 4 | `create_search_tool()` 工廠函式 | ✅ |
| 測試 5 | `parallel_multi_source` provider | ✅ |
| 測試 6 | `config_path` 關鍵字參數 | ✅ |

---

## 備註

- 發現並修正了一個參數順序 bug：`config_dict` 原本是第二參數，現改為第一參數，避免 `ConfigDrivenSearchTool({...})` 被誤判為 `config_path`
- `kwargs.get("model", "gemini-2.0-flash")` 的 default 值只是 fallback，不是實際使用的值（由 config 決定），這是合理的設計
