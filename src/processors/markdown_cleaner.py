"""
Markdown 清理 Processor

移除 LLM 輸出中的 Markdown 語法（**、##、### 等）。
"""

import re
from typing import Optional
from .base import Processor
from .registry import register


class MarkdownCleanerProcessor(Processor):
    """Markdown 清理 Processor"""

    processor_name = "markdown_cleaner"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text:
            return text

        # 0. 保護電話號碼格式 ***-****-****
        PHONE_PLACEHOLDER = "__PHONE_PROTECT__"
        phone_pattern = re.compile(r"(?:\d+-)?\*{3}-\*{3,4}-\*{3,4}")
        protected_phones = []

        def _protect_phone(m):
            protected_phones.append(m.group(0))
            return PHONE_PLACEHOLDER

        text = phone_pattern.sub(_protect_phone, text)

        # 1. 移除 **bold** 語法
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)

        # 2. 移除空 ****
        text = re.sub(r"\*\*\*\*", "", text)

        # 3. 移除 ### 三級標題
        text = re.sub(r"^###\s+", "", text, flags=re.MULTILINE)

        # 4. 移除 ## 二級標題
        text = re.sub(r"^##\s+", "", text, flags=re.MULTILINE)

        # 5. 移除 # 一級標題
        text = re.sub(r"^#\s+", "", text, flags=re.MULTILINE)

        # 6. 還原被保護的電話號碼
        for phone in protected_phones:
            text = text.replace(PHONE_PLACEHOLDER, phone, 1)

        return text


register(MarkdownCleanerProcessor)
