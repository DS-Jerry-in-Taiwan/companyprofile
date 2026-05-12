"""
格式統一 Processor

統一文本格式（標點、空格、換行）。
"""

import re
from typing import Optional
from .base import Processor
from .registry import register


class FormatNormalizerProcessor(Processor):
    """格式統一 Processor"""

    processor_name = "format_normalizer"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text:
            return text

        # 檢查是否包含 HTML 標籤
        has_html = "<" in text and ">" in text

        if has_html:
            return self._normalize_html_format(text)
        else:
            return self._normalize_plain_text_format(text)

    def _normalize_html_format(self, text: str) -> str:
        """統一 HTML 內容的格式"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(text, "html.parser")

        for tag in soup.find_all(True):
            if tag.string:
                normalized = self._normalize_plain_text_format(tag.string)
                tag.string = normalized

        result = str(soup)
        result = self._normalize_line_breaks(result)
        return result

    def _normalize_plain_text_format(self, text: str) -> str:
        """統一純文本格式"""
        text = self._normalize_punctuation(text)
        text = self._remove_extra_spaces(text)
        text = self._normalize_line_breaks(text)
        return text

    def _normalize_punctuation(self, text: str) -> str:
        """統一標點符號為中文標點"""
        punct_map = {
            ",": "，",
            "!": "！",
            "?": "？",
            ":": "：",
            ";": "；",
            "(": "（",
            ")": "）",
            "[": "［",
            "]": "］",
        }

        result = []
        i = 0
        while i < len(text):
            char = text[i]

            if char == ".":
                if (
                    i > 0
                    and i < len(text) - 1
                    and text[i - 1].isdigit()
                    and text[i + 1].isdigit()
                ):
                    result.append(char)
                elif i > 0 and text[i - 1 : i + 4] in ["http", "www."]:
                    result.append(char)
                elif i == len(text) - 1 or text[i + 1] in " \n\t":
                    result.append("。")
                else:
                    result.append(char)
            elif char == '"':
                result.append("「")
            elif char == "'":
                result.append("『")
            elif char == ":" and i > 0:
                if i >= 4 and text[i - 4 : i] == "http":
                    result.append(":")
                elif i >= 3 and text[i - 3 : i] == "ftp":
                    result.append(":")
                else:
                    result.append("：")
            elif char in punct_map:
                result.append(punct_map[char])
            else:
                result.append(char)

            i += 1

        return "".join(result)

    def _remove_extra_spaces(self, text: str) -> str:
        """移除多餘空格"""
        text = text.strip()
        text = text.replace("　", " ")
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\s+([，。！？；：])", r"\1", text)
        text = re.sub(r"([，。！？；：])\s+", r"\1", text)
        return text

    def _normalize_line_breaks(self, text: str) -> str:
        """統一換行格式"""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip("\n")
        return text


register(FormatNormalizerProcessor)
