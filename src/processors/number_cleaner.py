"""
數字格式清理 Processor

移除數字中的千位逗號（含全形逗號）。
"""

import re
from typing import Optional
from .base import Processor
from .registry import register


class NumberCleanerProcessor(Processor):
    """數字格式清理 Processor"""

    processor_name = "number_cleaner"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text:
            return text

        # 移除千位逗號 — 處理半形逗號
        while re.search(r"\d,\d{3}", text):
            text = re.sub(r"(\d),(\d{3})", r"\1\2", text)

        # 移除千位逗號 — 處理全形逗號
        while re.search(r"\d，\d{3}", text):
            text = re.sub(r"(\d)，(\d{3})", r"\1\2", text)

        return text


register(NumberCleanerProcessor)
