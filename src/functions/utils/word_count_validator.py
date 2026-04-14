# word_count_validator.py
"""
Phase 14 Stage 3: 字數檢核模組

新架構：Prompt 層控制 + 字數檢核 + 必要時 LLM 重寫

功能：
- 檢核 LLM 生成的內容是否在目標字數範圍內
- 若超出範圍，觸發重寫流程
- 建構重寫 prompt（要求保留風格與意涵，只做文字縮放）

字數範圍定義：
- Concise: 40-120 字
- Standard: 130-280 字
- Detailed: 280-700 字
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Literal

logger = logging.getLogger(__name__)

# 字數範圍定義（上下限）- Phase 14 Stage 3 放寬
WORD_COUNT_RANGES = {
    "concise": {"min": 40, "max": 120},
    "standard": {"min": 130, "max": 280},
    "detailed": {"min": 280, "max": 700},
}

# 觸發重寫的閾值（超出上限的百分比）
REWRITE_THRESHOLD = 0.20  # 超出上限 20% 時觸發重寫

# 最大重寫次數
MAX_REWRITE_ATTEMPTS = 2


@dataclass
class ValidationResult:
    """字數驗證結果"""

    is_valid: bool  # 是否在範圍內
    word_count: int  # 實際字數
    min_range: int  # 最小範圍
    max_range: int  # 最大範圍
    needs_rewrite: bool  # 是否需要重寫
    rewrite_reason: Optional[str] = None  # 重寫原因
    deviation: Optional[float] = None  # 偏離程度（百分比）


class WordCountValidator:
    """字數檢核器"""

    def __init__(
        self,
        ranges: Optional[dict] = None,
        rewrite_threshold: float = REWRITE_THRESHOLD,
        max_rewrite_attempts: int = MAX_REWRITE_ATTEMPTS,
    ):
        """
        初始化字數檢核器

        Args:
            ranges: 字數範圍定義，預設使用 WORD_COUNT_RANGES
            rewrite_threshold: 觸發重寫的閾值（超出上限百分比）
            max_rewrite_attempts: 最大重寫次數
        """
        self.ranges = ranges or WORD_COUNT_RANGES
        self.rewrite_threshold = rewrite_threshold
        self.max_rewrite_attempts = max_rewrite_attempts

    def count_words(self, text: str) -> int:
        """
        計算純文字字數（不含 HTML 標籤）

        Args:
            text: 輸入文字（可能是 HTML）

        Returns:
            純文字字數
        """
        if not text:
            return 0

        # 移除 HTML 標籤
        plain_text = re.sub(r"<[^>]+>", "", text)

        # 移除多餘空白
        plain_text = re.sub(r"\s+", "", plain_text)

        return len(plain_text)

    def validate(self, html_content: str, template_type: str) -> ValidationResult:
        """
        檢核字數是否在範圍內

        Args:
            html_content: LLM 生成的 HTML 內容
            template_type: 模板類型 (concise/standard/detailed)

        Returns:
            ValidationResult: 驗證結果
        """
        if not html_content:
            return ValidationResult(
                is_valid=False,
                word_count=0,
                min_range=0,
                max_range=0,
                needs_rewrite=False,
                rewrite_reason="內容為空",
            )

        # 取得該模板的字數範圍
        range_info = self.ranges.get(template_type.lower(), self.ranges["standard"])
        min_range = range_info["min"]
        max_range = range_info["max"]

        # 計算實際字數
        word_count = self.count_words(html_content)

        # 檢查是否在範圍內
        is_valid = min_range <= word_count <= max_range

        # 計算偏離程度
        deviation = None
        rewrite_reason = None
        needs_rewrite = False

        if word_count > max_range:
            # 超出上限
            deviation = (word_count - max_range) / max_range
            # 只有超出閾值才需要重寫
            needs_rewrite = deviation > self.rewrite_threshold
            rewrite_reason = (
                f"字數 {word_count} 超過上限 {max_range} "
                f"（偏離 {deviation * 100:.1f}%）"
            )
        elif word_count < min_range:
            # 低於下限
            deviation = (min_range - word_count) / min_range
            # 只有低於閾值才需要重寫
            needs_rewrite = deviation > self.rewrite_threshold
            rewrite_reason = (
                f"字數 {word_count} 低於下限 {min_range} "
                f"（偏離 {deviation * 100:.1f}%）"
            )

        logger.debug(
            f"[WordCountValidator] 模板: {template_type}, "
            f"字數: {word_count}, 範圍: {min_range}-{max_range}, "
            f"有效: {is_valid}, 需重寫: {needs_rewrite}"
        )

        return ValidationResult(
            is_valid=is_valid,
            word_count=word_count,
            min_range=min_range,
            max_range=max_range,
            needs_rewrite=needs_rewrite,
            rewrite_reason=rewrite_reason,
            deviation=deviation,
        )

    def needs_rewrite(self, result: ValidationResult) -> bool:
        """
        判斷是否需要重寫

        Args:
            result: ValidationResult 驗證結果

        Returns:
            bool: 是否需要重寫
        """
        # 超出閾值才需要重寫
        return result.needs_rewrite

    def build_rewrite_prompt(
        self,
        original_content: str,
        template_type: str,
        current_length: int,
        target_range: Tuple[int, int],
        rewrite_count: int = 0,
    ) -> str:
        """
        建構重寫 prompt，要求保留風格與意涵，只做文字縮放

        Args:
            original_content: 原始內容（HTML 格式）
            template_type: 模板類型
            current_length: 當前字數
            target_range: 目標字數範圍 (min, max)
            rewrite_count: 當前重寫次數（用於區分不同輪次）

        Returns:
            str: 重寫 prompt
        """
        template_names = {
            "concise": "精簡模式",
            "standard": "標準模式",
            "detailed": "詳細模式",
        }
        template_name = template_names.get(template_type.lower(), "標準模式")

        # 提取純文字內容用於重寫
        plain_content = re.sub(r"<[^>]+>", "", original_content)

        # 計算需要調整的幅度
        min_range, max_range = target_range
        if current_length > max_range:
            scale = "縮短"
            target_length = f"{min_range}-{max_range}字"
        else:
            scale = "擴展"
            target_length = f"{min_range}-{max_range}字"

        rewrite_prompt = f"""## 重寫任務（第 {rewrite_count + 1} 次）

### 任務描述
請將以下公司簡介進行文字縮放，使其字數符合 {target_length} 的目標範圍。

### 原始內容（{current_length} 字）
{plain_content}

### 目標範圍
- 最小字數：{min_range} 字
- 最大字數：{max_range} 字
- 當前字數：{current_length} 字

### 具體要求
1. **保留核心資訊**：公司名稱、主要業務、核心特色、成立年份等關鍵資訊必須保留
2. **保留表達風格**：維持原文的語氣、角度和專業程度
3. **只做文字縮放**：
   - 如需縮短：精簡冗餘描述、合併句子、移除不必要的修飾詞
   - 如需擴展：補充細節、豐富描述、增加相關資訊
4. **禁止事項**：
   - 不要添加「以下是...」「總之」等開頭語
   - 不要添加「...」或其他截斷符號
   - 不要改變敘述角度
5. **HTML 標籤保持完整**：如有 HTML 標籤，確保結構完整
6. **台灣用語**：使用台灣常用語彙

### 輸出格式
直接輸出重寫後的內容（HTML 或純文字皆可），無需額外說明。

請確保輸出後的字數在 {min_range}-{max_range} 字之間。
"""
        return rewrite_prompt

    def get_template_range(self, template_type: str) -> Tuple[int, int]:
        """
        取得指定模板的字數範圍

        Args:
            template_type: 模板類型

        Returns:
            Tuple[int, int]: (min, max)
        """
        range_info = self.ranges.get(template_type.lower(), self.ranges["standard"])
        return (range_info["min"], range_info["max"])

    def validate_and_suggest(self, html_content: str, template_type: str) -> dict:
        """
        驗證並提供改善建議

        Args:
            html_content: LLM 生成的內容
            template_type: 模板類型

        Returns:
            dict: 包含驗證結果和建議
        """
        result = self.validate(html_content, template_type)

        suggestions = []

        if result.word_count < result.min_range:
            suggestions.append(
                f"內容過短（{result.word_count} 字），建議補充 {result.min_range - result.word_count} 字"
            )
        elif result.word_count > result.max_range:
            suggestions.append(
                f"內容過長（{result.word_count} 字），建議刪減 {result.word_count - result.max_range} 字"
            )
        else:
            suggestions.append(f"字數符合要求（{result.word_count} 字）")

        return {
            "is_valid": result.is_valid,
            "word_count": result.word_count,
            "range": (result.min_range, result.max_range),
            "needs_rewrite": result.needs_rewrite,
            "suggestions": suggestions,
            "rewrite_reason": result.rewrite_reason,
        }


def count_words_in_html(html_content: str) -> int:
    """
    便捷函數：計算 HTML 中的純文字字數

    Args:
        html_content: HTML 內容

    Returns:
        int: 純文字字數
    """
    validator = WordCountValidator()
    return validator.count_words(html_content)


def validate_word_count(
    html_content: str,
    template_type: str,
    ranges: Optional[dict] = None,
) -> ValidationResult:
    """
    便捷函數：驗證字數

    Args:
        html_content: HTML 內容
        template_type: 模板類型
        ranges: 自定義字數範圍

    Returns:
        ValidationResult: 驗證結果
    """
    # 如果有自定義範圍，需要合併預設範圍以支援 fallback
    if ranges is not None:
        merged_ranges = dict(WORD_COUNT_RANGES)  # 複製預設範圍
        merged_ranges.update(ranges)  # 更新自定義範圍
        validator = WordCountValidator(ranges=merged_ranges)
    else:
        validator = WordCountValidator()
    return validator.validate(html_content, template_type)


def needs_rewrite(result: ValidationResult) -> bool:
    """
    便捷函數：判斷是否需要重寫

    Args:
        result: ValidationResult

    Returns:
        bool: 是否需要重寫
    """
    validator = WordCountValidator()
    return validator.needs_rewrite(result)
