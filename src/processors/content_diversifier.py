"""
內容多樣化 Processor

消除模板感，增加生成內容的多樣性和自然度。
"""

import logging
from typing import Optional
from .base import Processor
from .registry import register

logger = logging.getLogger(__name__)

# 嘗試導入 content_diversifier
try:
    from src.functions.utils.content_diversifier import diversify_content

    CONTENT_DIVERSIFIER_AVAILABLE = True
except ImportError as e:
    CONTENT_DIVERSIFIER_AVAILABLE = False
    logger.warning(f"content_diversifier 模組未找到，跳過多樣化處理: {e}")

    def diversify_content(text):
        return text


class ContentDiversifierProcessor(Processor):
    """內容多樣化 Processor"""

    processor_name = "content_diversifier"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text:
            return text

        try:
            from src.functions.utils.content_diversifier import diversify_content

            return diversify_content(text)
        except ImportError as e:
            logger.warning(f"content_diversifier 模組未找到，跳過多樣化處理: {e}")
            return text


register(ContentDiversifierProcessor)
