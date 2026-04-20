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

緩存機制的好處：
1. 避免重複創建昂貴的工具實例
2. 減少 API key 驗證次數
3. 提高後續請求的響應速度
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
    def _ensure_tools_registered(cls):
        """
        確保所有工具類別都已註冊

        內部使用，在列出或創建工具前調用
        """
        # 如果已經註冊過，直接返回
        if cls._tool_classes:
            return

        # 延遲導入避免循環依賴
        from src.services.search_tools import (
            TavilyBatchSearchTool,
            GeminiFewShotSearchTool,
            GeminiPlannerTavilyTool,
            ParallelMultiSourceTool,
            ParallelAspectSearchTool,
            ParallelFieldSearchTool,  # Phase19
        )

        # 註冊工具類別
        cls._tool_classes["tavily"] = TavilyBatchSearchTool
        cls._tool_classes["gemini_fewshot"] = GeminiFewShotSearchTool
        cls._tool_classes["gemini_planner_tavily"] = GeminiPlannerTavilyTool
        cls._tool_classes["parallel_multi_source"] = ParallelMultiSourceTool
        cls._tool_classes["parallel_aspect_search"] = ParallelAspectSearchTool
        cls._tool_classes["parallel_field_search"] = ParallelFieldSearchTool  # Phase19

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
        # 確保工具已註冊
        cls._ensure_tools_registered()

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
        cls._ensure_tools_registered()
        return list(cls._tool_classes.keys())
