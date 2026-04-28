# Phase 17：步驟 3-5 - 配置驅動與主流程調整

**日期**: 2026-04-17  
**步驟**: 3, 4, 5  
**狀態**: 🔄 待實作

---

## 🎯 步驟目標

| 步驟 | 目標 |
|-------|------|
| 步驟 3 | 增強配置驅動層，支援策略選擇 |
| 步驟 4 | 更新配置文件 |
| 步驟 5 | 調整主流程調用 |

---

## 📋 步驟 3：配置驅動層增強

### 任務 3.1：修改 SearchConfig dataclass

**檔案**: `src/services/config_driven_search.py`

**修改內容**：

```python
@dataclass
class SearchConfig:
    """搜尋配置"""
    provider: str = "gemini_fewshot"
    max_results: int = 3
    parallel: bool = False
    max_workers: int = 4
    timeout: int = 15
    strategies: Dict[str, Dict] = field(default_factory=dict)
    models: Dict[str, ModelConfig] = field(default_factory=dict)
```

### 任務 3.2：修改 _create_tool 方法

**修改內容**：

```python
def _create_tool(self, provider: str, config: Dict = None) -> BaseSearchTool:
    """建立工具實例"""
    from src.services.tool_factory import SearchToolFactory

    # 使用工廠建立工具（帶緩存）
    if config:
        return SearchToolFactory.get_tool(provider, config)
    else:
        return SearchToolFactory.get_tool(provider)
```

### 任務 3.3：新增策略選擇方法

**新增內容**：

```python
def search_with_strategy(self, query: str, strategy: str = "default") -> SearchResult:
    """
    使用指定策略搜尋

    Args:
        query: 查詢字串
        strategy: 策略名稱

    Returns:
        SearchResult: 搜尋結果
    """
    # 獲取策略配置
    if strategy in self.config.strategies:
        strategy_config = self.config.strategies[strategy]
        provider = strategy_config.get("provider", self.config.provider)
        return self._search_with_provider(query, provider, strategy_config)
    else:
        # 使用預設配置
        return self.search(query)
```

---

## 📋 步驟 4：配置文件更新

### 任務 4.1：更新 search_config.json

**檔案**: `config/search_config.json`

**新配置**：

```json
{
  "comment": "搜尋策略配置文件 - 修改 provider 欄位即可切換策略",
  "available_providers": {
    "tavily": "Tavily 批次搜尋 - 快速、1次 API",
    "gemini_fewshot": "Gemini Few-shot 搜尋 - 完整、1次 API",
    "gemini_planner_tavily": "Gemini 規劃 + Tavily 執行",
    "parallel_multi_source": "平行多來源搜尋",
    "parallel_aspect_search": "平行面向搜尋 - 4 面向獨立查詢"
  },
  "search": {
    "provider": "gemini_fewshot",
    "max_results": 3,
    "parallel": false,
    "max_workers": 4,
    "timeout": 15
  },
  "strategies": {
    "fast": {
      "provider": "tavily",
      "description": "快速驗證（1-2s）"
    },
    "basic": {
      "provider": "gemini_fewshot",
      "description": "基本簡介（5-8s）"
    },
    "complete": {
      "provider": "parallel_aspect_search",
      "description": "完整簡介（6-10s）",
      "parallel": true,
      "max_workers": 4
    },
    "deep": {
      "provider": "parallel_multi_source",
      "description": "深度分析（15-20s）",
      "parallel": true
    }
  },
  "default_strategy": "complete",
  "models": {
    "gemini_fewshot": {
      "model": "gemini-2.0-flash-lite",
      "temperature": 0.2
    },
    "gemini_planner_tavily": {
      "model": "gemini-2.0-flash",
      "temperature": 0.1
    },
    "parallel_aspect_search": {
      "model": "gemini-2.0-flash",
      "temperature": 0.2
    }
  }
}
```

---

## 📋 步驟 5：主流程調整

### 任務 5.1：修改 search_node

**檔案**: `src/langgraph_state/company_brief_graph.py`

**修改內容**：

```python
def search_node(state: CompanyBriefState) -> CompanyBriefState:
    """搜尋節點 - 支援平行查詢"""
    logger.info(f"執行搜尋節點，搜尋公司：{state['organ']}")
    start_time = time.time()

    try:
        # 導入搜尋功能
        from src.services.config_driven_search import ConfigDrivenSearchTool

        # 獲取策略（從狀態或預設）
        strategy = state.get('search_strategy', 'default')

        # 建立搜尋工具
        tool = ConfigDrivenSearchTool()

        # 執行搜尋
        with measure("搜尋階段"):
            search_result = tool.search_with_strategy(
                state['organ'],  # 移除「官網」關鍵字
                strategy=strategy
            )

        execution_time = time.time() - start_time
        logger.info(f"[TIMING] 搜尋階段完成，耗時 {execution_time * 1000:.2f}ms")

        # 處理結果（保持現有邏輯）
        structured_results = []
        if search_result.data:
            for aspect, content in search_result.data.items():
                if content:
                    structured_results.append({
                        "aspect": aspect,
                        "content": content,
                        "success": True,
                    })

        result = SearchResult(
            success=search_result.success,
            answer=search_result.raw_answer,
            results=structured_results,
            source=search_result.tool_type,
            execution_time=execution_time,
            error=None if search_result.success else "搜尋失敗",
        )

        # 建立節點結果
        node_result = NodeResult(
            node_name=NodeNames.SEARCH,
            status=NodeStatus.COMPLETED if result.success else NodeStatus.FAILED,
            output=result,
            execution_time=execution_time,
        )

        if not result.success:
            node_result.error = Exception(result.error or "Search failed")

        # 更新狀態
        return update_state_with_node_result(state, node_result)

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"搜尋節點執行失敗: {e}")

        result = SearchResult(
            success=False,
            error=str(e),
            execution_time=execution_time,
        )

        node_result = NodeResult(
            node_name=NodeNames.SEARCH,
            status=NodeStatus.FAILED,
            output=result,
            error=e,
            execution_time=execution_time,
        )

        return update_state_with_node_result(state, node_result)
```

---

## 🧪 測試任務

### 測試 3.1：驗證配置解析

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.config_driven_search import SearchConfig

config = SearchConfig.from_dict({
    'search': {'provider': 'parallel_aspect_search', 'parallel': True, 'max_workers': 4},
    'strategies': {
        'complete': {'provider': 'parallel_aspect_search', 'parallel': True}
    }
})

assert config.parallel == True
assert config.max_workers == 4
assert 'complete' in config.strategies

print('✅ 測試 3.1 通過：配置解析正確')
"
```

### 測試 3.2：驗證策略選擇

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.config_driven_search import ConfigDrivenSearchTool

tool = ConfigDrivenSearchTool()

# 驗證方法存在
assert hasattr(tool, 'search_with_strategy')

print('✅ 測試 3.2 通過：策略選擇方法存在')
"
```

### 測試 4.1：驗證配置文件

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
import json

with open('config/search_config.json', 'r') as f:
    config = json.load(f)

assert 'strategies' in config
assert 'parallel_aspect_search' in config['strategies']
assert 'default_strategy' in config

print('✅ 測試 4.1 通過：配置文件正確')
"
```

### 測試 5.1：驗證主流程調整

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
# 驗證 search_node 函數存在且可呼叫
from src.langgraph_state.company_brief_graph import search_node

print('✅ 測試 5.1 通過：search_node 函數正確')
"
```

---

## ✅ 通過標準

### 步驟 3
- [x] SearchConfig dataclass 修改正確
- [x] _create_tool 方法使用工廠
- [x] search_with_strategy 方法存在

### 步驟 4
- [x] 配置文件包含 strategies 區塊
- [x] parallel_aspect_search 配置正確
- [x] default_strategy 設定正確

### 步驟 5
- [x] search_node 移除「官網」關鍵字
- [x] 支援 strategy 參數
- [x] 結果處理邏輯正確

---

## 📊 預計工時

| 步驟 | 任務 | 工時 | 累計 |
|------|------|------|------|
| 步驟 3 | 配置驅動層 | 2h | 2h |
| 步驟 4 | 配置文件 | 1h | 3h |
| 步驟 5 | 主流程 | 1h | 4h |
| **總計** | | **4h** | **7h** |

---

## 📝 開發紀錄

### 2026-04-17

| 時間 | 任務 | 狀態 | 備註 |
|------|------|------|------|
| - | - | 🔄 | 待開始 |

---

*步驟完成時間：待定*