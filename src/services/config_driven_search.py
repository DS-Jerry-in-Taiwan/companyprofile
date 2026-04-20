"""
配置驅動搜尋工具
===================

透過配置文件切換不同的搜尋模組

設計理念：
- 主流程完全不需要改動，只需要修改配置文件即可切換策略
- 支援熱重載和動態切換
- 統一的 search() 介面

配置範例 (config/search_config.json):
{
    "search": {
        "provider": "gemini_fewshot",  // 可選: tavily, gemini_fewshot, gemini_planner_tavily
        "max_results": 3,
        "temperature": 0.2
    }
}

支援的策略：
- tavily: Tavily 批次搜尋（快速 ~1s）
- gemini_fewshot: Gemini Few-shot 搜尋（完整 ~5-30s）
- gemini_planner_tavily: Gemini 規劃 + Tavily 執行（~18s）

使用方式：
```python
# 方式一：最簡單（推薦）
from src.services.config_driven_search import search
result = search("澳霸有限公司")  # 自動根據配置執行

# 方式二：使用類別
from src.services.config_driven_search import ConfigDrivenSearchTool
search_tool = ConfigDrivenSearchTool()  # 自動讀取配置
result = search_tool.search("澳霸有限公司")

# 方式三：動態切換
tool = ConfigDrivenSearchTool()
tool.switch_provider("tavily")  # 動態切換到 Tavily
result = tool.search("澳霸有限公司")
```

切換策略：
只需要修改 config/search_config.json 中的 provider 欄位：
- "tavily": 使用 Tavily 批次搜尋
- "gemini_fewshot": 使用 Gemini Few-shot 搜尋
- "gemini_planner_tavily": 使用 Gemini 規劃 + Tavily 執行

相關檔案：
- search_tools.py: 工具層核心（工廠 + 工具類）
- config/search_config.json: 搜尋策略配置
"""

import os
import sys
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# 動態計算專案根目錄
_CURRENT_FILE = os.path.abspath(__file__)
# /home/ubuntu/projects/OrganBriefOptimization/src/services/config_driven_search.py
# 需要往上 3 層: services -> src -> 專案根目錄
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
# 加入系統路徑
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

PROJECT_ROOT = _PROJECT_ROOT


# ===== 配置類別 =====
@dataclass
class ModelConfig:
    """模型配置"""

    model: str = "gemini-2.0-flash"
    temperature: float = 0.2


@dataclass
class SearchConfig:
    """搜尋配置"""

    provider: str = "gemini_fewshot"  # 預設使用 gemini_fewshot
    max_results: int = 3
    parallel: bool = False
    max_workers: int = 4
    timeout: int = 15
    strategies: Dict[str, Dict] = field(default_factory=dict)
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    default_strategy: str = "basic"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchConfig":
        """從字典創建配置"""
        search_data = data.get("search", {})
        models = {}
        for name, cfg in data.get("models", {}).items():
            models[name] = ModelConfig(
                model=cfg.get("model", "gemini-2.0-flash"),
                temperature=cfg.get("temperature", 0.2),
            )
        return cls(
            provider=search_data.get("provider", "gemini_fewshot"),
            max_results=search_data.get("max_results", 3),
            parallel=search_data.get("parallel", False),
            max_workers=search_data.get("max_workers", 4),
            timeout=search_data.get("timeout", 15),
            strategies=data.get("strategies", {}),
            default_strategy=data.get("default_strategy", "basic"),
            models=models,
        )


# ===== 配置驅動搜尋工具 =====
class ConfigDrivenSearchTool:
    """
    配置驅動搜尋工具

    根據配置文件自動選擇和執行相應的搜尋工具
    主流程完全不需要改動，只需要修改配置文件即可切換策略
    """

    # 預設配置文件路徑
    DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "search_config.json")

    def __init__(
        self,
        config_dict: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
    ):
        """
        初始化配置驅動搜尋工具

        Args:
            config_dict: 直接傳入的配置字典（優先於 config_path）
            config_path: 配置文件路徑（JSON 格式）
        """
        # 載入配置
        if config_dict is not None:
            # config_dict 傳入完整結構（含 search + models 區塊）
            # 確保 models 不為 None，否則 from_dict 會出錯
            if "models" not in config_dict:
                config_dict = {**config_dict, "models": {}}
            self.config = SearchConfig.from_dict(config_dict)
        elif config_path:
            self.config = self._load_config(config_path)
        else:
            self.config = self._load_config(self.DEFAULT_CONFIG_PATH)

        # 根據配置創建實際的搜尋工具
        self._tool = self._create_tool()

        # 設定檔案路徑（用於熱重載）
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH

    def _load_config(self, config_path: str) -> SearchConfig:
        """載入配置文件"""
        if not os.path.exists(config_path):
            print(f"⚠️ 配置文件不存在: {config_path}")
            print(f"   使用預設配置")
            return SearchConfig()

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        return SearchConfig.from_dict(config_data)

    def _create_tool(self, provider: Optional[str] = None):
        """根據配置創建搜尋工具"""
        from src.services.tool_factory import SearchToolFactory

        provider = (provider or self.config.provider).lower()

        print(f"🔧 配置驅動搜尋工具初始化")
        print(f"   Provider: {provider}")
        print(f"   Max Results: {self.config.max_results}")

        # 根據 provider 創建對應的工具
        if provider == "tavily":
            return SearchToolFactory.get_tool(
                "tavily",
                {"max_results": self.config.max_results},
            )
        elif provider == "gemini_fewshot":
            model_cfg = self.config.models.get("gemini_fewshot", ModelConfig())
            return SearchToolFactory.get_tool(
                "gemini_fewshot",
                {
                    "model": model_cfg.model,
                    "temperature": model_cfg.temperature,
                },
            )
        elif provider == "gemini_planner_tavily":
            model_cfg = self.config.models.get("gemini_planner_tavily", ModelConfig())
            return SearchToolFactory.get_tool(
                "gemini_planner_tavily",
                {
                    "max_results": self.config.max_results,
                    "model": model_cfg.model,
                    "temperature": model_cfg.temperature,
                },
            )
        elif provider == "parallel_multi_source":
            # 平行多來源搜尋
            return SearchToolFactory.get_tool(
                "parallel_multi_source",
                {"sources": ["tavily", "gemini_fewshot"], "timeout": 15},
            )
        elif provider == "parallel_aspect_search":
            # 平行面向搜尋
            model_cfg = self.config.models.get("parallel_aspect_search", ModelConfig())
            return SearchToolFactory.get_tool(
                "parallel_aspect_search",
                {
                    "model": model_cfg.model,
                    "temperature": model_cfg.temperature,
                    "max_workers": self.config.max_workers,
                    "timeout": self.config.timeout,
                },
            )
        elif provider == "parallel_field_search":
            # Phase19: 平行字段搜尋
            model_cfg = self.config.models.get("parallel_field_search", ModelConfig())
            return SearchToolFactory.get_tool(
                "parallel_field_search",
                {
                    "model": model_cfg.model,
                    "temperature": model_cfg.temperature,
                    "max_workers": 7,  # 7 個字段
                    "timeout": self.config.timeout,
                },
            )
        else:
            print(f"⚠️ 未知的 provider: {provider}，使用預設 gemini_fewshot")
            return SearchToolFactory.get_tool("gemini_fewshot")

    def search(self, query: str, **kwargs) -> "SearchResult":
        """
        執行搜尋（主流程調用這個）

        Args:
            query: 搜尋查詢
            **kwargs: 額外參數

        Returns:
            SearchResult: 統一的搜尋結果
        """
        from src.services.search_tools import SearchResult

        print(f"\n📤 配置驅動搜尋執行")
        print(f"   Query: {query}")
        print(f"   Provider: {self.config.provider}")

        result = self._tool.search(query, **kwargs)

        print(f"   ✅ 成功")
        print(f"   ⏱️  耗時: {result.elapsed_time:.2f}s")
        print(f"   📝 回答長度: {result.answer_length} 字")

        return result

    def search_with_strategy(
        self, query: str, strategy: Optional[str] = None
    ) -> "SearchResult":
        """
        使用指定策略搜尋

        Args:
            query: 查詢字串
            strategy: 策略名稱（如果為 None，使用預設策略）

        Returns:
            SearchResult: 搜尋結果
        """
        from src.services.search_tools import SearchResult

        # 如果沒有指定策略，使用預設策略
        if strategy is None:
            strategy = self.config.default_strategy

        print(f"\n📤 策略驅動搜尋執行")
        print(f"   Query: {query}")
        print(f"   Strategy: {strategy}")

        # 獲取策略配置
        if strategy in self.config.strategies:
            strategy_config = self.config.strategies[strategy]
            provider = strategy_config.get("provider", self.config.provider)
            print(f"   Provider: {provider}")

            # 創建該策略的工具
            tool = self._create_tool(provider)
            result = tool.search(query, **strategy_config)
        else:
            # 使用預設配置
            print(f"   ⚠️ 策略 {strategy} 不存在，使用預設配置")
            result = self._tool.search(query)

        print(f"   ✅ 成功")
        print(f"   ⏱️  耗時: {result.elapsed_time:.2f}s")
        print(f"   📝 回答長度: {result.answer_length} 字")

        return result

    def reload_config(self):
        """熱重載配置（不改變物件，重新創建工具）"""
        print(f"\n🔄 熱重載配置...")
        self.config = self._load_config(self.config_path)
        self._tool = self._create_tool()
        print(f"   ✅ 配置已重載")

    def switch_provider(self, provider: str):
        """
        動態切換 provider（不改變配置檔案）

        Args:
            provider: 新的 provider 名稱
        """
        print(f"\n🔄 動態切換 Provider: {self.config.provider} -> {provider}")
        self.config.provider = provider
        self._tool = self._create_tool()


# ===== 便捷函式 =====
# 單例模式，全域只需要一個實例
_instance: Optional[ConfigDrivenSearchTool] = None


def get_search_tool(config_path: Optional[str] = None) -> ConfigDrivenSearchTool:
    """
    取得全域搜尋工具實例（單例）

    Args:
        config_path: 配置文件路徑

    Returns:
        ConfigDrivenSearchTool: 搜尋工具實例
    """
    global _instance

    if _instance is None or config_path is not None:
        _instance = ConfigDrivenSearchTool(config_path)

    return _instance


def search(query: str, **kwargs) -> "SearchResult":
    """
    便捷搜尋函式（最簡單的調用方式）

    Args:
        query: 搜尋查詢

    Returns:
        SearchResult: 搜尋結果
    """
    from src.services.search_tools import SearchResult

    tool = get_search_tool()
    return tool.search(query, **kwargs)
