"""
Taiwan Terms Converter Plugin

此模組提供中國用語轉換為台灣用語的功能。

主要功能:
1. 簡繁字符轉換 (使用 OpenCC)
2. 詞彙對照替換 (使用 Taiwan.md 詞庫)
3. 支援 Lambda 和本地環境

使用方式:
    >>> from taiwan_terms import TaiwanTermsConverter
    >>> converter = TaiwanTermsConverter()
    >>> result = converter.convert("我们的软件产品")
    >>> print(result.text)
    我們的軟體產品
"""

from .converter import TaiwanTermsConverter
from .types import ConvertOptions, ConvertResult, ConversionStats

__version__ = "0.1.0"
__all__ = [
    "TaiwanTermsConverter",
    "ConvertOptions", 
    "ConvertResult",
    "ConversionStats",
]

# 初始化日誌
import logging
logger = logging.getLogger(__name__)