"""
配置驅動搜尋工具
===================

透過配置文件切換不同的搜尋模組

配置範例 (config.json):
{
    "search": {
        "provider": "gemini_fewshot",  // 可選: tavily, gemini_fewshot, gemini_planner_tavily
        "max_results": 3,
        "temperature": 0.2
    }
}

使用方式：
```python
from config_driven_search import ConfigDrivenSearchTool

# 主流程 - 完全不用改
search_tool = ConfigDrivenSearchTool()  # 自動讀取配置
result = search_tool.search("澳霸有限公司")  # 根據配置執行
```
"""

import os
import sys
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts", "stage3_test"))


# ===== 配置類別 =====
@dataclass
class SearchConfig:
    """搜尋配置"""

    provider: str = "gemini_fewshot"  # 預設使用 gemini_fewshot
    max_results: int = 3
    temperature: float = 0.2
    model: str = "gemini-2.0-flash"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchConfig":
        """從字典創建配置"""
        return cls(
            provider=data.get("provider", "gemini_fewshot"),
            max_results=data.get("max_results", 3),
            temperature=data.get("temperature", 0.2),
            model=data.get("model", "gemini-2.0-flash"),
        )


# ===== 配置驅動搜尋工具 =====
class ConfigDrivenSearchTool:
    """
    配置驅動搜尋工具

    根據配置文件自動選擇和執行相應的搜尋工具
    主流程完全不需要改動，只需要修改配置文件即可切換策略
    """

    # 預設配置文件路徑
    DEFAULT_CONFIG_PATH = os.path.join(
        PROJECT_ROOT, "scripts", "stage3_test", "search_config.json"
    )

    def __init__(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化配置驅動搜尋工具

        Args:
            config_path: 配置文件路徑（JSON 格式）
            config_dict: 直接傳入的配置字典（優先於 config_path）
        """
        # 載入配置
        if config_dict is not None:
            self.config = SearchConfig.from_dict(config_dict.get("search", {}))
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

        return SearchConfig.from_dict(config_data.get("search", {}))

    def _create_tool(self):
        """根據配置創建搜尋工具"""
        from search_tools import create_search_tool, BaseSearchTool

        provider = self.config.provider.lower()

        print(f"🔧 配置驅動搜尋工具初始化")
        print(f"   Provider: {provider}")
        print(f"   Max Results: {self.config.max_results}")

        # 根據 provider 創建對應的工具
        if provider == "tavily":
            return create_search_tool(
                "tavily",
                max_results=self.config.max_results,
            )
        elif provider == "gemini_fewshot":
            return create_search_tool(
                "gemini_fewshot",
                model=self.config.model,
                temperature=self.config.temperature,
            )
        elif provider == "gemini_planner_tavily":
            return create_search_tool(
                "gemini_planner_tavily",
                max_results=self.config.max_results,
            )
        else:
            print(f"⚠️ 未知的 provider: {provider}，使用預設 gemini_fewshot")
            return create_search_tool("gemini_fewshot")

    def search(self, query: str, **kwargs) -> "SearchResult":
        """
        執行搜尋（主流程調用這個）

        Args:
            query: 搜尋查詢
            **kwargs: 額外參數

        Returns:
            SearchResult: 統一的搜尋結果
        """
        print(f"\n📤 配置驅動搜尋執行")
        print(f"   Query: {query}")
        print(f"   Provider: {self.config.provider}")

        result = self._tool.search(query, **kwargs)

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
    tool = get_search_tool()
    return tool.search(query, **kwargs)


# ===== 測試 =====
if __name__ == "__main__":
    print("=" * 70)
    print("配 置 驅 動 搜 索 工 具 測 試")
    print("=" * 70)

    # 測試配置文件
    config_path = os.path.join(
        PROJECT_ROOT, "scripts", "stage3_test", "search_config.json"
    )

    # 確保配置文件存在
    if not os.path.exists(config_path):
        print(f"⚠️ 配置文件不存在，建立預設配置...")
        default_config = {
            "search": {
                "provider": "gemini_fewshot",
                "max_results": 3,
                "temperature": 0.2,
                "model": "gemini-2.0-flash",
            }
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"   ✅ 已建立: {config_path}")

    # 建立配置驅動搜尋工具
    print(f"\n1. 建立 ConfigDrivenSearchTool...")
    tool = ConfigDrivenSearchTool(config_path)

    # 執行搜尋
    print(f"\n2. 執行搜尋...")
    result = tool.search("澳霸有限公司")

    print(f"\n3. 結果:")
    print(f"   成功: {result.success}")
    print(f"   類型: {result.tool_type}")
    print(f"   耗時: {result.elapsed_time:.2f}s")

    if result.data:
        print(f"\n   📊 結構化資料:")
        for k, v in result.data.items():
            print(f"      {k}: {str(v)[:50]}...")

    # 測試動態切換
    print(f"\n4. 測試動態切換 Provider...")
    tool.switch_provider("tavily")
    result2 = tool.search("澳霸有限公司")
    print(f"   新 Provider 結果: {result2.elapsed_time:.2f}s")

    print(f"\n{'=' * 70}")
    print("測 試 完 成")
    print("=" * 70)
