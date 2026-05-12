"""
HTML 清理 Processor

使用 bleach 清理 HTML，只允許安全的標籤。
"""

import bleach
from typing import Optional
from .base import Processor
from .registry import register


class HtmlSanitizerProcessor(Processor):
    """HTML 清理 Processor"""

    processor_name = "html_sanitizer"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text:
            return text
        return bleach.clean(
            text,
            tags=["p", "b", "i", "ul", "li", "br"],
            strip=True,
        )


register(HtmlSanitizerProcessor)
