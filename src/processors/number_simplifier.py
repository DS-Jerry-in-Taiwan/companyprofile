"""
數字簡化 Processor

將大數字簡化為自然單位（億/萬）。
"""

import re
from typing import Optional
from .base import Processor
from .registry import register

# 轉換門檻
_SIMPLIFY_THRESHOLD_YI = 100_000_000  # 1億
_SIMPLIFY_THRESHOLD_WAN = 10_000      # 1萬

# 數字簡化 — 只處理後綴為「元」的大數字
_SIMPLIFY_PATTERN = re.compile(r"(\d{5,})\s*元")


class NumberSimplifierProcessor(Processor):
    """數字簡化 Processor"""

    processor_name = "number_simplifier"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text:
            return text
        return _SIMPLIFY_PATTERN.sub(self._simplify_number_match, text)

    @staticmethod
    def _simplify_number_match(match: re.Match) -> str:
        """將 regex match 中的數字轉換為自然單位"""
        num_str = match.group(1)
        num = int(num_str)

        if num >= _SIMPLIFY_THRESHOLD_YI:
            val = num / _SIMPLIFY_THRESHOLD_YI
            if val == int(val):
                return f"{int(val)}億元"
            else:
                return f"{val:.1f}億元"
        elif num >= _SIMPLIFY_THRESHOLD_WAN:
            val = num / _SIMPLIFY_THRESHOLD_WAN
            if val == int(val):
                return f"{int(val)}萬元"
            else:
                return f"{val:.1f}萬元"
        return match.group(0)


register(NumberSimplifierProcessor)
