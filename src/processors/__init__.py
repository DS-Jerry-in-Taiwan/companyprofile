"""
Processors Package - 後處理 Pipeline 的可插拔 Processor 單元

提供基於抽象類別的 Processor 架構，支援配置驅動的 Pipeline 執行。
"""

from .registry import register, get_processor, list_processors
from .pipeline import PostProcessPipeline

# 匯入所有 Processor 模組以觸發註冊
from . import (
    html_sanitizer,
    markdown_cleaner,
    verbose_remover,
    taiwan_converter,
    format_normalizer,
    content_diversifier,
    template_differentiator,
    number_cleaner,
    number_simplifier,
    perspective_fixer,
    sensitive_filter,
)

__all__ = [
    "register",
    "get_processor",
    "list_processors",
    "PostProcessPipeline",
]
