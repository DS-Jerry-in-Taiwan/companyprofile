"""
搜尋提供者
==========

統一使用 SearchResult dataclass
"""

# 設定路徑（放在最前面）
import os
import sys

_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from .base_provider import BaseSearchProvider
from .tavily_search import TavilySearchProvider, tavily_search, get_tavily_provider
from .gemini_search import (
    GeminiFlashSearchProvider,
    gemini_flash_search,
    get_gemini_provider,
)

__all__ = [
    "BaseSearchProvider",
    "TavilySearchProvider",
    "tavily_search",
    "get_tavily_provider",
    "GeminiFlashSearchProvider",
    "gemini_flash_search",
    "get_gemini_provider",
]
