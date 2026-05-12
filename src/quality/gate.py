"""
QualityGate - 品質閘門

在 LLM 產出後檢查內容品質，決定是否通過或需要重試。
"""

import logging
from typing import Callable, List, Tuple

from src.quality.checks import (
    check_company_name,
    check_min_length,
    check_no_truncation,
    check_normal_start,
    check_no_artifact_markers,
    check_no_repetition,
    check_no_template_leftovers,
    check_chinese_ratio,
)

logger = logging.getLogger(__name__)

# 檢查函式型別
CheckFunc = Callable[..., Tuple[bool, str]]


class QualityGate:
    """品質閘門，依序執行檢查項目"""

    # 預設檢查項目（名稱, 函式, 額外參數名）
    DEFAULT_CHECKS = [
        ("company_name", check_company_name, ["organ", "title", "summary"]),
        ("min_length", check_min_length, []),
        ("no_truncation", check_no_truncation, []),
        ("normal_start", check_normal_start, []),
        ("no_artifact_markers", check_no_artifact_markers, []),
        ("no_repetition", check_no_repetition, []),
        ("no_template_leftovers", check_no_template_leftovers, []),
        ("chinese_ratio", check_chinese_ratio, []),
    ]

    def __init__(self, checks: list = None):
        self.checks = checks or self.DEFAULT_CHECKS

    def check(self, body_html: str, **kwargs) -> Tuple[bool, List[str]]:
        """
        執行所有檢查

        Args:
            body_html: LLM 產出的 body_html 內容
            **kwargs: 傳遞給檢查函式的額外參數（如 organ）

        Returns:
            (passed: bool, issues: List[str])
        """
        issues = []
        for name, func, extra_params in self.checks:
            # 收集參數
            args = [body_html]
            for param in extra_params:
                if param in kwargs:
                    args.append(kwargs[param])
                else:
                    args.append(None)
            try:
                passed, reason = func(*args)
                if not passed:
                    issues.append(f"[{name}] {reason}")
                    logger.warning(f"品質檢查失敗: [{name}] {reason}")
            except Exception as e:
                logger.error(f"品質檢查異常 [{name}]: {e}")
                issues.append(f"[{name}] 檢查異常: {e}")

        return len(issues) == 0, issues
