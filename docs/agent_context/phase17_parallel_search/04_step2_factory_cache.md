# Phase 17：步驟 2 - 工具工廠與緩存機制

**日期**: 2026-04-17  
**步驟**: 2  
**狀態**: 🔄 待實作

---

## 🎯 步驟目標

實現工具單例模式，避免重複創建工具實例

---

## 📋 開發任務

### 任務 2.1：新增 SearchToolFactory 類別

**檔案**: `src/services/tool_factory.py`（新檔案）

**代碼**：

```python
"""
搜尋工具工廠
===========

實現工具單例模式，支援工具緩存。

使用方式：
```python
from src.services.tool_factory import SearchToolFactory

# 獲取工具（帶緩存）
tool = SearchToolFactory.get_tool("parallel_aspect_search")

# 重置緩存（用於測試）
SearchToolFactory.reset()
```
"""

import os
import sys
from typing import Dict, Any, Optional

# 動態計算專案根目錄
_CURRENT_FILE = os.path.abspath(__file__)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class SearchToolFactory:
    """
    搜尋工具工廠（單例模式）

    特性：
    - 工具緩存：避免重複創建
    - 動態註冊：支援新增工具類別
    - 配置驅動：根據配置建立工具
    """

    # 工具緩存
    _tools: Dict[str, Any] = {}

    # 工具類別註冊表
    _tool_classes: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, tool_class: type):
        """
        註冊工具類別

        Args:
            name: 工具名稱
            tool_class: 工具類別
        """
        cls._tool_classes[name] = tool_class

    @classmethod
    def get_tool(cls, provider: str, config: Optional[Dict] = None) -> Any:
        """
        獲取工具實例（帶緩存）

        Args:
            provider: 工具名稱
            config: 工具配置（首次創建時需要）

        Returns:
            工具實例
        """
        # 如果緩存中沒有，就創建一個
        if provider not in cls._tools:
            cls._tools[provider] = cls._create_tool(provider, config or {})

        return cls._tools[provider]

    @classmethod
    def _create_tool(cls, provider: str, config: Dict) -> Any:
        """
        創建工具實例

        Args:
            provider: 工具名稱
            config: 工具配置

        Returns:
            工具實例
        """
        # 延遲導入避免循環依賴
        from src.services.search_tools import (
            TavilyBatchSearchTool,
            GeminiFewShotSearchTool,
            GeminiPlannerTavilyTool,
            ParallelMultiSourceTool,
            ParallelAspectSearchTool,
        )

        # 註冊工具類別（如果還沒註冊）
        if "tavily" not in cls._tool_classes:
            cls._tool_classes["tavily"] = TavilyBatchSearchTool
        if "gemini_fewshot" not in cls._tool_classes:
            cls._tool_classes["gemini_fewshot"] = GeminiFewShotSearchTool
        if "gemini_planner_tavily" not in cls._tool_classes:
            cls._tool_classes["gemini_planner_tavily"] = GeminiPlannerTavilyTool
        if "parallel_multi_source" not in cls._tool_classes:
            cls._tool_classes["parallel_multi_source"] = ParallelMultiSourceTool
        if "parallel_aspect_search" not in cls._tool_classes:
            cls._tool_classes["parallel_aspect_search"] = ParallelAspectSearchTool

        # 創建工具
        if provider in cls._tool_classes:
            return cls._tool_classes[provider](**config)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    @classmethod
    def reset(cls):
        """
        重置工廠（清除緩存）

        用於：
        - 測試環境重置
        - 配置變更後重新載入
        """
        cls._tools = {}

    @classmethod
    def list_providers(cls) -> list:
        """
        列出所有支援的工具

        Returns:
            工具名稱列表
        """
        return list(cls._tool_classes.keys())
```

---

## 🧪 測試任務

### 測試 2.1：驗證工具緩存

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.tool_factory import SearchToolFactory

# 重置緩存
SearchToolFactory.reset()

# 獲取工具
tool1 = SearchToolFactory.get_tool('parallel_aspect_search')
tool2 = SearchToolFactory.get_tool('parallel_aspect_search')

# 驗證是同一個實例
assert tool1 is tool2, '應該是同一個實例'

print('✅ 測試 2.1 通過：工具緩存正確')
"
```

### 測試 2.2：驗證單例模式

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.tool_factory import SearchToolFactory

# 重置
SearchToolFactory.reset()

# 第一次獲取
tool1 = SearchToolFactory.get_tool('parallel_aspect_search')

# 第二次獲取（應該是同一個）
tool2 = SearchToolFactory.get_tool('parallel_aspect_search')

# 驗證
assert tool1 is tool2, '單例模式：應該是同一個實例'
print(f'tool1 id: {id(tool1)}')
print(f'tool2 id: {id(tool2)}')
print('✅ 測試 2.2 通過：單例模式正確')
"
```

### 測試 2.3：驗證 reset 功能

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.tool_factory import SearchToolFactory

# 重置
SearchToolFactory.reset()

# 獲取工具
tool1 = SearchToolFactory.get_tool('parallel_aspect_search')

# 重置
SearchToolFactory.reset()

# 再次獲取（應該是新實例）
tool2 = SearchToolFactory.get_tool('parallel_aspect_search')

# 驗證
assert tool1 is not tool2, 'reset 後應該是新實例'
print('✅ 測試 2.3 通過：reset 功能正確')
"
```

### 測試 2.4：驗證工具列表

```bash
cd /home/ubuntu/projects/OrganBriefOptimization && python -c "
from src.services.tool_factory import SearchToolFactory

# 列出支援的工具
providers = SearchToolFactory.list_providers()

print(f'支援的工具: {providers}')
assert 'parallel_aspect_search' in providers
assert 'gemini_fewshot' in providers
assert 'tavily' in providers

print('✅ 測試 2.4 通過：工具列表正確')
"
```

---

## ✅ 通過標準

- [x] SearchToolFactory 類別存在
- [x] 工具緩存正確
- [x] 單例模式正確
- [x] reset 功能正確
- [x] list_providers 功能正確

---

## 📊 預計工時

| 任務 | 工時 |
|------|------|
| 任務 2.1：實作類別 | 1h |
| 任務 2.2-2.4：測試 | 1h |
| **總計** | **2h** |

---

## 📝 開發紀錄

### 2026-04-17

| 時間 | 任務 | 狀態 | 備註 |
|------|------|------|------|
| - | - | 🔄 | 待開始 |

---

*步驟完成時間：待定*