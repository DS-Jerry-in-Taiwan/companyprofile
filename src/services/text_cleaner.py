"""
Text Cleaner Service
文字清洗服務，負責處理和轉換文字內容
"""

import re
import unicodedata
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TextCleaner:
    """文字清洗服務"""

    def __init__(
        self,
        remove_extra_whitespace: bool = True,
        normalize_unicode: bool = True,
        remove_special_chars: bool = False,
        min_length: int = 10,
    ):
        """
        初始化文字清洗器

        Args:
            remove_extra_whitespace: 是否移除多餘空白
            normalize_unicode: 是否正規化 Unicode
            remove_special_chars: 是否移除特殊字元
            min_length: 最小文字長度
        """
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_special_chars = remove_special_chars
        self.min_length = min_length

    def clean(self, text: str) -> str:
        """
        執行文字清洗

        Args:
            text: 原始文字

        Returns:
            str: 清洗後的文字
        """
        if not text:
            return ""

        # Unicode 正規化
        if self.normalize_unicode:
            text = self._normalize_unicode(text)

        # 移除多餘空白
        if self.remove_extra_whitespace:
            text = self._remove_extra_whitespace(text)

        # 移除特殊字元
        if self.remove_special_chars:
            text = self._remove_special_characters(text)

        # 移除 HTML 實體
        text = self._remove_html_entities(text)

        # 移除 URL
        text = self._remove_urls(text)

        # 移除電子郵件
        text = self._remove_emails(text)

        # 移除多餘的標點符號
        text = self._remove_excessive_punctuation(text)

        return text.strip()

    def clean_for_llm(self, text: str, max_length: Optional[int] = None) -> str:
        """
        為 LLM 準備文字（更嚴格的清洗）

        Args:
            text: 原始文字
            max_length: 最大長度

        Returns:
            str: 清洗後適合 LLM 的文字
        """
        # 基本清洗
        text = self.clean(text)

        # 移除控制字元
        text = self._remove_control_characters(text)

        # 規範化引號和破折號
        text = self._normalize_quotes_and_dashes(text)

        # 截斷到最大長度
        if max_length and len(text) > max_length:
            text = text[:max_length].rsplit(" ", 1)[0] + "..."

        return text

    def extract_chinese_text(self, text: str) -> str:
        """
        提取中文文字

        Args:
            text: 原始文字

        Returns:
            str: 提取的中文文字
        """
        # 匹配中文字符和標點符號
        chinese_pattern = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+")
        chinese_text = "".join(chinese_pattern.findall(text))

        return chinese_text.strip()

    def extract_english_text(self, text: str) -> str:
        """
        提取英文文字

        Args:
            text: 原始文字

        Returns:
            str: 提取的英文文字
        """
        # 匹配英文字母、數字和基本標點
        english_pattern = re.compile(r'[a-zA-Z0-9\s.,!?;:\'"-]+')
        english_text = " ".join(english_pattern.findall(text))

        return english_text.strip()

    def count_tokens_estimate(self, text: str) -> int:
        """
        估算 token 數量

        Args:
            text: 文字內容

        Returns:
            int: 估算的 token 數
        """
        # 計算中文字符數
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))

        # 計算其他字符數（主要是英文）
        other_chars = len(text) - chinese_chars

        # 估算：中文約 1.5 個字/Token，英文約 4 個字元/Token
        estimated_tokens = int(chinese_chars / 1.5 + other_chars / 4)

        return estimated_tokens

    def _normalize_unicode(self, text: str) -> str:
        """正規化 Unicode 字符"""
        return unicodedata.normalize("NFKC", text)

    def _remove_extra_whitespace(self, text: str) -> str:
        """移除多餘空白"""
        # 替換各種空白字符為單個空格
        text = re.sub(r"[\t\n\r\f\v]+", " ", text)
        # 移除多餘空格
        text = re.sub(r" {2,}", " ", text)
        return text

    def _remove_special_characters(self, text: str) -> str:
        """移除特殊字元（保留中文、英文、數字和基本標點）"""
        # 保留中文、英文、數字和常用標點
        pattern = re.compile(
            r"[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"
            r'a-zA-Z0-9\s.,!?;:\'"-（），。！？；：、]+'
        )
        return pattern.sub("", text)

    def _remove_html_entities(self, text: str) -> str:
        """移除 HTML 實體"""
        # 常見 HTML 實體
        html_entities = {
            "&nbsp;": " ",
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
            "&copy;": "©",
            "&reg;": "®",
            "&trade;": "™",
        }

        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)

        # 移除其他 HTML 實體
        text = re.sub(r"&[a-zA-Z]+;", "", text)
        text = re.sub(r"&#\d+;", "", text)

        return text

    def _remove_urls(self, text: str) -> str:
        """移除 URL"""
        url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        return url_pattern.sub("", text)

    def _remove_emails(self, text: str) -> str:
        """移除電子郵件"""
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        return email_pattern.sub("", text)

    def _remove_excessive_punctuation(self, text: str) -> str:
        """移除過多的標點符號"""
        # 替換重複的標點為單個
        text = re.sub(r"([.,!?;:])\1+", r"\1", text)
        return text

    def _remove_control_characters(self, text: str) -> str:
        """移除控制字元"""
        # 移除控制字元（保留換行和製表符）
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        return text

    def _normalize_quotes_and_dashes(self, text: str) -> str:
        """規範化引號和破折號"""
        # 引號規範化
        text = text.replace("「", '"').replace("」", '"')
        text = text.replace("『", "'").replace("』", "'")
        text = text.replace("“", '"').replace("”", '"')
        text = text.replace("‘", "'").replace("’", "'")

        # 破折號規範化
        text = text.replace("—", "--")
        text = text.replace("–", "-")

        return text


class TextSplitter:
    """文字分割器"""

    def __init__(
        self, chunk_size: int = 1000, overlap: int = 100, separator: str = "\n"
    ):
        """
        初始化文字分割器

        Args:
            chunk_size: 每個區塊的大小
            overlap: 重疊大小
            separator: 分隔符
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separator = separator

    def split(self, text: str) -> list:
        """
        分割文字為多個區塊

        Args:
            text: 原始文字

        Returns:
            list: 文字區塊列表
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            if end >= len(text):
                chunks.append(text[start:])
                break

            # 尋找最近的分隔符
            separator_pos = text.rfind(self.separator, start, end)

            if separator_pos == -1 or separator_pos <= start:
                # 找不到分隔符，使用空格
                space_pos = text.rfind(" ", start, end)
                if space_pos == -1 or space_pos <= start:
                    # 找不到空格，強制分割
                    separator_pos = end
                else:
                    separator_pos = space_pos

            chunks.append(text[start:separator_pos])
            start = separator_pos + 1 - self.overlap

        return chunks
