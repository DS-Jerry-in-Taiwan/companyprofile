"""
視角修正 Processor

將第三人稱用詞取代為第一人稱，解決語體漂移問題。
"""

from typing import Optional
from .base import Processor
from .registry import register

# 第三人稱 → 第一人稱 對照表
_THIRD_PERSON_PATTERNS = {
    "該公司": "我們",
    "該企業": "我們",
    "這家公司": "我們",
}


class PerspectiveFixerProcessor(Processor):
    """視角修正 Processor"""

    processor_name = "perspective_fixer"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        """
        將第三人稱用詞取代為第一人稱。

        只有在文本中已存在「我們」時才執行取代，避免誤改。
        """
        if not text or "我們" not in text:
            return text

        for third, first in _THIRD_PERSON_PATTERNS.items():
            if third in text:
                text = text.replace(third, first)

        return text


register(PerspectiveFixerProcessor)
