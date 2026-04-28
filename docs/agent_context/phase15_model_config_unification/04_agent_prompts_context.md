# Phase 15 - Agent 提示詞上下文

**最後更新**: 2026-04-15

## 給 Development Agent 的逐步提示詞

---

### 第一步（工項 1）：修改 `SearchConfig` dataclass

**目標檔案**: `src/services/config_driven_search.py`

**任務**：
1. 在 `SearchConfig` dataclass 上方新增一個 `ModelConfig` dataclass
2. 在 `SearchConfig` 中新增 `models: Dict[str, ModelConfig] = field(default_factory=dict)` 欄位
3. 更新 `from_dict()` 方法，從 `data.get("models", {})` 解析並建立 `models` 字典

請參考文件 `docs/agent_context/phase15_model_config_unification/phase15-model-config-unification.md` 第 77-103 行的程式碼範例實作。

完成後用以下測試驗證：

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.config_driven_search import SearchConfig

config = SearchConfig.from_dict({
    'search': {'provider': 'gemini_fewshot', 'max_results': 2},
    'models': {
        'gemini_fewshot': {'model': 'gemini-2.0-flash-lite', 'temperature': 0.2},
        'gemini_planner_tavily': {'model': 'gemini-2.0-flash', 'temperature': 0.1}
    }
})
print(f'models: {config.models}')
print(f'gemini_fewshot model: {config.models.get(\"gemini_fewshot\").model}')
print(f'gemini_planner_tavily model: {config.models.get(\"gemini_planner_tavily\").model}')
print('✅ 工項 1 驗證通過')
"
```

通過後回報，繼續下一個工項。

---

### 第二步（工項 2）：更新 `_create_tool()` 傳遞模型參數

**目標檔案**: `src/services/config_driven_search.py`

**任務**：
1. 在 `_create_tool()` 中找到 `gemini_fewshot` 的分支
2. 把原本只傳 `model=self.config.model` 改成從 `self.config.models.get("gemini_fewshot", ModelConfig())` 讀取
3. 在 `gemini_planner_tavily` 的分支中新增 `model=` 和 `temperature=` 參數（目前是完全沒傳的）

請參考文件第 110-126 行的程式碼範例。

完成後用以下測試驗證：

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
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

通過後回報，繼續下一個工項。

---

### 第三步（工項 3）：修改 `GeminiPlannerTavilyTool` 接收參數

**目標檔案**: `src/services/search_tools.py`

**任務**：
1. 在 `GeminiPlannerTavilyTool.__init__` 中新增：
   ```python
   self.model = kwargs.get("model", "gemini-2.0-flash")
   self.temperature = kwargs.get("temperature", 0.1)
   ```
2. 在 `search()` 方法中，找到 `generate_content` 呼叫，把原本寫死的 `model="gemini-2.0-flash"` 改成 `model=self.model`
3. 同時把 `temperature` 也改成從實例變數讀取

請參考文件第 131-151 行。

完成後用以下測試驗證：

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
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

通過後回報，繼續下一個工項。

---

### 第四步（工項 4）：更新 `config/search_config.json`

**目標檔案**: `config/search_config.json`

**任務**：將檔案內容更新為新 schema：

```json
{
  "comment": "搜尋策略配置文件 - 修改 provider 欄位即可切換策略",
  "available_providers": {
    "tavily": "Tavily 批次搜尋 - 快速、1次 API，自然語言回應",
    "gemini_fewshot": "Gemini Few-shot 搜尋 - 完整、1次 API、JSON 格式",
    "gemini_planner_tavily": "Gemini 規劃 + Tavily 執行 - 彈性、多步驟",
    "parallel_multi_source": "平行多來源搜尋 - 同時執行 Tavily + Gemini，取最快結果 + 多源驗證"
  },
  "search": {
    "provider": "gemini_fewshot",
    "max_results": 3
  },
  "models": {
    "gemini_fewshot": {
      "model": "gemini-2.0-flash-lite",
      "temperature": 0.2
    },
    "gemini_planner_tavily": {
      "model": "gemini-2.0-flash",
      "temperature": 0.1
    }
  }
}
```

完成後用以下測試驗證：

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.config_driven_search import ConfigDrivenSearchTool

t = ConfigDrivenSearchTool()
print(f'provider: {t.config.provider}')
print(f'gemini_fewshot model: {t.config.models.get(\"gemini_fewshot\").model}')
print(f'gemini_planner_tavily model: {t.config.models.get(\"gemini_planner_tavily\").model}')
print('✅ 工項 4 驗證通過')
"
```

通過後回報，繼續下一個工項。

---

### 第五步（工項 5）：更新 `.env.example`

**目標檔案**: `.env.example`

**任務**：在檔案末尾新增說明區塊：

```bash
# 搜尋模型配置（可選，預設在 config/search_config.json 中設定）
# SEARCH_GEMINI_MODEL=gemini-2.0-flash-lite
# SEARCH_GEMINI_TEMPERATURE=0.2
```

---

### 第六步（工項 6）：最終驗證

執行完整整合測試：

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.config_driven_search import ConfigDrivenSearchTool

t = ConfigDrivenSearchTool()

print(f'=== Phase 15 最終驗證 ===')
print(f'provider: {t.config.provider}')
print(f'max_results: {t.config.max_results}')
print()

for name in ['gemini_fewshot', 'gemini_planner_tavily']:
    mc = t.config.models.get(name)
    print(f'{name}:')
    print(f'  model: {mc.model}')
    print(f'  temperature: {mc.temperature}')

# 確認 search_tools.py 中沒有硬編碼模型名稱
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
    print()
    print('❌ 仍有硬編碼：')
    for h in hardcoded:
        print(f'  {h}')
else:
    print()
    print('✅ search_tools.py 中無硬編碼模型名稱')

print()
print('✅ Phase 15 全部完成')
"
```

完成全部 6 個工項且最終驗證通過後，請提供完整摘要報告。
