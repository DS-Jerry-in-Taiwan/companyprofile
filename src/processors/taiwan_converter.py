"""
台灣用語轉換 Processor

將文字中的中國用語轉換為台灣用語。
"""

import logging
from typing import Optional
from .base import Processor
from .registry import register

logger = logging.getLogger(__name__)

# Phase 14.1: 嘗試導入台灣用語轉換器
try:
    from src.plugins.taiwan_terms import TaiwanTermsConverter, ConvertOptions

    TAIWAN_TERMS_AVAILABLE = True
    # 建立全局轉換器實例（懶加載）
    _taiwan_converter = None

    def get_taiwan_converter():
        """取得台灣用語轉換器（單例）"""
        global _taiwan_converter
        if _taiwan_converter is None:
            _taiwan_converter = TaiwanTermsConverter(
                ConvertOptions(
                    enable_opencc=True,
                    enable_term_mapping=True,
                    preserve_english=True,
                    raise_on_error=False,
                )
            )
        return _taiwan_converter

except ImportError as e:
    TAIWAN_TERMS_AVAILABLE = False
    logger.warning(f"台灣用語轉換器不可用 - {e}")

    def get_taiwan_converter():
        return None


class TaiwanConverterProcessor(Processor):
    """台灣用語轉換 Processor"""

    processor_name = "taiwan_converter"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text or not TAIWAN_TERMS_AVAILABLE:
            return text

        text = text.strip()
        if not text:
            return text

        original_len = len(text)
        chars_converted = 0

        # 檢查是否包含 HTML 標籤
        has_html = "<" in text and ">" in text
        import bs4

        if has_html:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(text, "html.parser")

            for text_node in soup.find_all(string=True):
                original_text = text_node.strip()
                if original_text:
                    converter = get_taiwan_converter()
                    result = converter.convert(original_text)
                    if result.success():
                        text_node.replace_with(bs4.NavigableString(result.text))
                        chars_converted += (
                            result.chars_converted
                            if hasattr(result, "chars_converted")
                            else 0
                        )
                    else:
                        logger.warning(f"台灣用語轉換失敗: {result.error}")

            result_text = str(soup)
        else:
            converter = get_taiwan_converter()
            result = converter.convert(text)
            if result.success():
                chars_converted = (
                    result.chars_converted if hasattr(result, "chars_converted") else 0
                )
                result_text = result.text
            else:
                logger.warning(f"台灣用語轉換失敗: {result.error}")
                result_text = text

        logger.info(
            f"[Taiwan Terms] 轉換前: {original_len} 字, "
            f"轉換後: {len(result_text)} 字, 轉換字元數: {chars_converted}"
        )
        return result_text


register(TaiwanConverterProcessor)
