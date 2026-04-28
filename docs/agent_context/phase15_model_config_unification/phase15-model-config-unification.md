# Phase 15：模型配置統一管理

## 目標

將散落在各處的模型配置（`config/search_config.json` + `search_tools.py`）統一集中到 `config/search_config.json` 的 `models` 區塊，消除所有硬編碼。

## 現有問題

| 位置 | 目前值 | 問題 |
|------|--------|------|
| `config/search_config.json` 第13行 | `"model": "gemini-2.0-flash-lite"` | 放在 `search` 底下，schema 不夠明確 |
| `search_tools.py` 第401行 `GeminiPlannerTavilyTool` | `model="gemini-2.0-flash"` | **完全寫死**，config 完全沒效 |

根本原因：`config_driven_search.py` 的 `_create_tool()` 只把 `model` 傳給 `gemini_fewshot`，`gemini_planner_tavily` 完全沒拿到。

## 解決方案

### 新 Schema：`config/search_config.json`

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

### 架構對應圖

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
│    ├── gemini_planner_tavily  → ✅ 從 config 讀（目前是硬編碼）
│    └── parallel_multi_source  → 從子工具繼承
         │
         ▼
search_tools.py
├── GeminiFewShotSearchTool     → 接收 model/temp 參數 ✅
└── GeminiPlannerTavilyTool     → 接收 model/temp 參數 ✅（目前是硬編碼）
```

## 工項清單

### 工項 1：修改 `SearchConfig` dataclass
**檔案**: `src/services/config_driven_search.py`

新增 `models` 欄位到 `SearchConfig` dataclass：

```python
@dataclass
class ModelConfig:
    """模型配置"""
    model: str = "gemini-2.0-flash"
    temperature: float = 0.2

@dataclass
class SearchConfig:
    provider: str = "gemini_fewshot"
    max_results: int = 3
    models: Dict[str, ModelConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchConfig":
        models = {}
        for name, cfg in data.get("models", {}).items():
            models[name] = ModelConfig(
                model=cfg.get("model", "gemini-2.0-flash"),
                temperature=cfg.get("temperature", 0.2),
            )
        return cls(
            provider=data.get("provider", "gemini_fewshot"),
            max_results=data.get("max_results", 3),
            models=models,
        )
```

### 工項 2：更新 `_create_tool()` 傳遞模型參數
**檔案**: `src/services/config_driven_search.py`

把各 provider 的 model 從 config 拿出來傳給 factory：

```python
elif provider == "gemini_planner_tavily":
    model_cfg = self.config.models.get("gemini_planner_tavily", ModelConfig())
    return create_search_tool(
        "gemini_planner_tavily",
        max_results=self.config.max_results,
        model=model_cfg.model,          # ← 新增
        temperature=model_cfg.temperature,  # ← 新增
    )
elif provider == "gemini_fewshot":
    model_cfg = self.config.models.get("gemini_fewshot", ModelConfig())
    return create_search_tool(
        "gemini_fewshot",
        model=model_cfg.model,
        temperature=model_cfg.temperature,
    )
```

### 工項 3：修改 `GeminiPlannerTavilyTool` 接收參數
**檔案**: `src/services/search_tools.py`

```python
class GeminiPlannerTavilyTool(BaseSearchTool):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ...
        self.model = kwargs.get("model", "gemini-2.0-flash")  # 從 kwargs 讀取
        self.temperature = kwargs.get("temperature", 0.1)

    def search(self, query: str, **kwargs) -> SearchResult:
        # ...
        planner_response = self.gemini_client.models.generate_content(
            model=self.model,  # ← 使用實例變數，不再寫死
            # ...
        )
```

同時移除原本寫死的：
```python
# 移除這一行：
model="gemini-2.0-flash",  # 原本在 line 401 寫死
```

### 工項 4：更新 `config/search_config.json`
**檔案**: `config/search_config.json`

套用新的 schema（見上方「解決方案」章節）。

### 工項 5：更新 `.env.example`
**檔案**: `.env.example`

新增搜尋模型說明（可選，用於未來支援環境變數覆寫）：

```bash
# 搜尋模型配置（可選，預設在 config/search_config.json 中設定）
# SEARCH_GEMINI_MODEL=gemini-2.0-flash-lite
# SEARCH_GEMINI_TEMPERATURE=0.2
```

### 工項 6：驗證測試

```bash
# 測試各 provider 都正確讀取模型
cd /home/ubuntu/projects/OrganBriefOptimization

# 直接測試搜尋工具工廠
python -c "
from src.services.config_driven_search import ConfigDrivenSearchTool

# 測試 gemini_fewshot
t1 = ConfigDrivenSearchTool({'search': {'provider': 'gemini_fewshot', 'max_results': 2}})
print(f'gemini_fewshot model: {t1.config.models.get(\"gemini_fewshot\", {}).model}')

# 測試 gemini_planner_tavily
t2 = ConfigDrivenSearchTool({'search': {'provider': 'gemini_planner_tavily', 'max_results': 2}})
print(f'gemini_planner_tavily model: {t2.config.models.get(\"gemini_planner_tavily\", {}).model}')

print('✅ 模型配置統一管理測試通過')
"
```

## 預期產出

- `src/services/config_driven_search.py` — `SearchConfig` + `_create_tool()` 更新
- `src/services/search_tools.py` — `GeminiPlannerTavilyTool` 移除硬編碼
- `config/search_config.json` — 新 schema
- `.env.example` — 新增說明

## 預期影響範圍

| 範圍 | 影響 |
|------|------|
| 搜尋模組 | ✅ 完全向後相容（只是把原本的行為移到 config） |
| 主流程 LangGraph | ✅ 無影響 |
| Layer 5/6 標籤生成 | ✅ 無影響（使用 `llm_service.py` 的 Gemini） |

## 成功標準

1. `config/search_config.json` 中的 `models.gemini_fewshot.model` 改變時，`gemini_fewshot` provider 實際使用的模型跟著變
2. `config/search_config.json` 中的 `models.gemini_planner_tavily.model` 改變時，`gemini_planner_tavily` provider 實際使用的模型跟著變
3. `search_tools.py` 中不再有任何模型名稱字面量（`gemini-2.0-flash-lite`、`gemini-2.0-flash`）
4. 所有模型配置只存在於 `config/search_config.json` 一個地方
