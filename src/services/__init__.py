"""
Services Package
================

數據檢索與前處理模組的服務類別

主要模組：
- tavily_search.py: Tavily API 搜尋服務
- search_tools.py: 搜尋工具層（工廠 + 策略工具）
- config_driven_search.py: 配置驅動搜尋工具
- data_retrieval_service.py: 數據檢索服務
- llm_service.py: LLM 生成服務

搜尋工具層使用方式：
```python
# 方式一：最簡單（推薦）
from src.services.config_driven_search import search
result = search("公司名稱")

# 方式二：建立工具實例
from src.services.config_driven_search import ConfigDrivenSearchTool
tool = ConfigDrivenSearchTool()
result = tool.search("公司名稱")

# 方式三：直接建立工具
from src.services.search_tools import create_search_tool
tool = create_search_tool("tavily")
result = tool.search("公司名稱")
```

詳見：
- search_tools.py: 工具層核心（工廠 + 工具類）
- config_driven_search.py: 配置驅動實作
"""

from .base_search_provider import BaseSearchProvider, SearchError
from .base_scraper import BaseScraper, ScrapingError, AntiScrapingError, ScrapingResult
from .serper_search import SerperSearchProvider
from .web_scraper import WebScraper
from .text_cleaner import TextCleaner, TextSplitter
from .data_retrieval_service import (
    DataRetrievalService,
    create_data_retrieval_service,
    process_company_data_retrieval,
)

# 搜尋工具層
from .search_tools import (
    SearchToolType,
    SearchResult,
    BaseSearchTool,
    SearchToolFactory,
    create_search_tool,
    search_with_tool,
)

from .config_driven_search import (
    ConfigDrivenSearchTool,
    get_search_tool,
    search,
    SearchConfig,
)

__all__ = [
    # 原有導出
    "BaseSearchProvider",
    "SearchError",
    "BaseScraper",
    "ScrapingError",
    "AntiScrapingError",
    "ScrapingResult",
    "SerperSearchProvider",
    "WebScraper",
    "TextCleaner",
    "TextSplitter",
    "DataRetrievalService",
    "create_data_retrieval_service",
    "process_company_data_retrieval",
    # 新增搜尋工具層
    "SearchToolType",
    "SearchResult",
    "BaseSearchTool",
    "SearchToolFactory",
    "create_search_tool",
    "search_with_tool",
    "ConfigDrivenSearchTool",
    "get_search_tool",
    "search",
    "SearchConfig",
]
