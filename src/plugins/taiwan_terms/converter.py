"""
台灣用語轉換器核心模組

提供中國用語轉換為台灣用語的主要功能：
1. 簡繁字符轉換（使用 OpenCC 或內建轉換表）
2. 詞彙對照替換（使用 Taiwan.md 詞庫）
3. 效能優化與統計
"""

import os
import re
import time
import logging
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache

from .types import ConvertOptions, ConvertResult, ConversionStats, ConversionError
from .loader import get_loader

logger = logging.getLogger(__name__)


class TaiwanTermsConverter:
    """台灣用語轉換器"""

    def __init__(self, options: Optional[ConvertOptions] = None):
        """
        初始化轉換器

        Args:
            options: 轉換選項，如未提供則使用預設值
        """
        self.options = options or ConvertOptions()

        # OpenCC 轉換器（懶加載）
        self._opencc_converter = None

        # 詞庫載入器
        self._loader = get_loader()

        # 效能快取
        self._stats_cache = {}

        logger.debug(f"轉換器初始化完成，選項: {self.options}")

    def convert(
        self, text: str, options: Optional[ConvertOptions] = None
    ) -> ConvertResult:
        """
        將文字中的中國用語轉換為台灣用語

        Args:
            text: 輸入文字
            options: 轉換選項（覆寫建構子選項）

        Returns:
            ConvertResult 物件
        """
        start_time = time.time()

        # 使用傳入選項或預設選項
        current_options = options or self.options

        # 初始化結果物件
        result = ConvertResult(original_text=text, stats=ConversionStats())

        try:
            # 輸入驗證
            if not text or not isinstance(text, str):
                result.text = text or ""
                result.stats.input_length = 0
                result.stats.output_length = 0
                result.stats.total_time_ms = (time.time() - start_time) * 1000
                return result

            # 記錄輸入長度
            result.stats.input_length = len(text)

            # 錯誤收集列表
            errors = []

            # Step 1: OpenCC 簡繁字符轉換
            processed_text = text
            opencc_time = 0.0

            if current_options.enable_opencc:
                try:
                    opencc_start = time.time()
                    processed_text = self._convert_with_opencc(
                        processed_text, current_options.opencc_mode
                    )
                    opencc_time = (time.time() - opencc_start) * 1000
                    result.stats.opencc_time_ms = opencc_time

                    # 估算轉換的字符數（簡單估算）
                    if text and processed_text:
                        # 計算不同的字符數
                        diff_chars = sum(
                            1 for a, b in zip(text, processed_text) if a != b
                        )
                        result.stats.opencc_chars_converted = diff_chars
                except Exception as e:
                    if current_options.raise_on_error:
                        raise
                    error_msg = f"OpenCC轉換失敗: {e}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

            # Step 2: 詞彙對照替換
            mapping_time = 0.0

            if current_options.enable_term_mapping:
                try:
                    mapping_start = time.time()
                    processed_text, replaced_terms = self._replace_terms(
                        processed_text,
                        precompile_regex=current_options.precompile_regex,
                    )
                    mapping_time = (time.time() - mapping_start) * 1000
                    result.stats.term_mapping_time_ms = mapping_time
                    result.stats.terms_replaced = len(replaced_terms)
                    result.stats.terms_matched = replaced_terms
                except Exception as e:
                    if current_options.raise_on_error:
                        raise
                    error_msg = f"詞彙替換失敗: {e}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

            # Step 3: 保留英文處理（如有需要）
            if current_options.preserve_english:
                # 目前先跳過，未來可實作英文保留邏輯
                pass

            # 記錄輸出長度和總時間
            result.text = processed_text
            result.stats.output_length = len(processed_text)

            total_time = (time.time() - start_time) * 1000
            result.stats.total_time_ms = total_time
            result.stats.loading_time_ms = (
                self._loader.get_loading_time() if self._loader.is_loaded() else 0.0
            )

            logger.debug(
                f"轉換完成: {result.stats.input_length} → {result.stats.output_length} 字, "
                f"耗時 {total_time:.2f}ms, 替換 {result.stats.terms_replaced} 個詞彙"
            )

            # 如果有錯誤，設置錯誤訊息
            if errors:
                result.error = "; ".join(errors)

            return result

        except Exception as e:
            error_msg = f"轉換過程發生錯誤: {str(e)}"
            logger.error(error_msg)

            if current_options.raise_on_error:
                raise ConversionError(error_msg) from e

            result.error = error_msg
            result.text = text  # 錯誤時返回原始文字
            result.stats.total_time_ms = (time.time() - start_time) * 1000

            return result

    def _convert_with_opencc(self, text: str, mode: str = "s2twp") -> str:
        """
        使用 OpenCC 進行簡繁字符轉換

        Args:
            text: 輸入文字
            mode: OpenCC 轉換模式

        Returns:
            轉換後文字
        """
        # 懶加載 OpenCC 轉換器
        if self._opencc_converter is None:
            self._opencc_converter = self._create_opencc_converter(mode)

        if self._opencc_converter is None:
            logger.warning("OpenCC 轉換器不可用，跳過字符轉換")
            return text

        try:
            return self._opencc_converter(text)
        except Exception as e:
            logger.error(f"OpenCC 轉換錯誤: {e}")
            # 回退到簡單轉換
            return self._simple_convert(text)

    def _create_opencc_converter(self, mode: str):
        """
        建立 OpenCC 轉換器

        嘗試載入 opencc-python，失敗時使用內建簡單轉換
        """
        try:
            # 嘗試導入 opencc-python
            import opencc

            logger.info(f"使用 OpenCC 轉換器，模式: {mode}")
            opencc_instance = opencc.OpenCC(mode)

            # 建立包裝函數以統一介面
            def opencc_wrapper(text):
                return opencc_instance.convert(text)

            return opencc_wrapper
        except ImportError:
            logger.warning("opencc-python 未安裝，使用內建簡繁轉換")
            # 回退到簡單轉換
            return self._simple_convert
        except Exception as e:
            logger.error(f"建立 OpenCC 轉換器失敗: {e}")
            return None

    def _simple_convert(self, text: str) -> str:
        """
        簡單簡繁轉換（內建轉換表）

        只處理常見的一對一簡繁轉換，用於 OpenCC 不可用時
        """
        # 常見簡繁對照表（部分）
        simple_mapping = {
            "国": "國",
            "产": "產",
            "为": "為",
            "发": "發",
            "经": "經",
            "过": "過",
            "这": "這",
            "个": "個",
            "时": "時",
            "会": "會",
            "说": "說",
            "话": "話",
            "来": "來",
            "去": "去",
            "在": "在",
            "的": "的",
            "和": "和",
            "是": "是",
            "了": "了",
            "有": "有",
            "不": "不",
            "人": "人",
            "我": "我",
            "他": "他",
            "她": "她",
            "它": "它",
            "们": "們",
            "你": "你",
            "您": "您",
            "好": "好",
            "吗": "嗎",
            "呢": "呢",
            "啊": "啊",
            "呀": "呀",
            "哦": "哦",
            "嗯": "嗯",
            "哈": "哈",
            "嘿": "嘿",
            "啦": "啦",
            "吧": "吧",
            "哪": "哪",
            "那": "那",
            "这": "這",
            "些": "些",
            "么": "麼",
            "什": "什",
            "怎": "怎",
            "么": "麼",
            "样": "樣",
            "都": "都",
            "很": "很",
            "太": "太",
            "真": "真",
            "假": "假",
            "对": "對",
            "错": "錯",
            "上": "上",
            "下": "下",
            "左": "左",
            "右": "右",
            "前": "前",
            "后": "後",
            "里": "裡",
            "外": "外",
            "中": "中",
            "大": "大",
            "小": "小",
            "多": "多",
            "少": "少",
            "高": "高",
            "低": "低",
            "长": "長",
            "短": "短",
            "宽": "寬",
            "窄": "窄",
            "厚": "厚",
            "薄": "薄",
            "重": "重",
            "轻": "輕",
            "快": "快",
            "慢": "慢",
            "新": "新",
            "旧": "舊",
            "好": "好",
            "坏": "壞",
            "美": "美",
            "丑": "醜",
            "强": "強",
            "弱": "弱",
            "热": "熱",
            "冷": "冷",
            "干": "乾",
            "湿": "濕",
            "硬": "硬",
            "软": "軟",
            "亮": "亮",
            "暗": "暗",
            "响": "響",
            "静": "靜",
            "香": "香",
            "臭": "臭",
            "甜": "甜",
            "苦": "苦",
            "酸": "酸",
            "辣": "辣",
            "咸": "鹹",
            "淡": "淡",
            "油": "油",
            "腻": "膩",
            "清": "清",
            "浊": "濁",
            "浓": "濃",
            "稀": "稀",
            "密": "密",
            "疏": "疏",
            "粗": "粗",
            "细": "細",
            "圆": "圓",
            "方": "方",
            "尖": "尖",
            "平": "平",
            "滑": "滑",
            "糙": "糙",
            "光": "光",
            "暗": "暗",
        }

        # 簡單轉換
        result = []
        for char in text:
            result.append(simple_mapping.get(char, char))

        return "".join(result)

    def _replace_terms(
        self, text: str, precompile_regex: bool = True
    ) -> Tuple[str, list]:
        """
        使用詞庫替換詞彙

        Args:
            text: 輸入文字
            precompile_regex: 是否使用預編譯的正則表達式

        Returns:
            (替換後文字, 被替換的詞彙列表)
        """
        # 載入詞庫（懶加載）
        terms_dict, regex_pattern = self._loader.load_terms()

        if not terms_dict or not text:
            return text, []

        replaced_terms = []

        if precompile_regex and regex_pattern:
            # 使用預編譯的正則表達式一次性匹配
            def replacement(match):
                matched = match.group(0)
                if matched in terms_dict:
                    replaced_terms.append(matched)
                    return terms_dict[matched]
                return matched

            processed_text = regex_pattern.sub(replacement, text)
        else:
            # 回退到逐一替換（較慢）
            processed_text = text
            for src_term, dst_term in terms_dict.items():
                if src_term in processed_text:
                    replaced_terms.append(src_term)
                    processed_text = processed_text.replace(src_term, dst_term)

        return processed_text, replaced_terms

    def batch_convert(
        self, texts: list, options: Optional[ConvertOptions] = None
    ) -> list:
        """
        批次轉換多個文字

        Args:
            texts: 文字列表
            options: 轉換選項

        Returns:
            ConvertResult 列表
        """
        return [self.convert(text, options) for text in texts]

    def get_stats(self) -> Dict[str, Any]:
        """取得轉換器統計資訊"""
        return {
            "terms_loaded": self._loader.get_terms_count(),
            "loader_loaded": self._loader.is_loaded(),
            "loading_time_ms": self._loader.get_loading_time(),
            "opencc_available": self._opencc_converter is not None,
        }

    def clear_cache(self):
        """清除快取（用於測試）"""
        self._loader.clear_cache()
        self._opencc_converter = None
        logger.info("轉換器快取已清除")


# 建立全局轉換器實例（單例模式）
_default_converter = None


def get_converter(options: Optional[ConvertOptions] = None) -> TaiwanTermsConverter:
    """
    取得全局轉換器實例

    Args:
        options: 轉換選項

    Returns:
        TaiwanTermsConverter 實例
    """
    global _default_converter

    if _default_converter is None:
        _default_converter = TaiwanTermsConverter(options)

    return _default_converter


def convert(text: str, options: Optional[ConvertOptions] = None) -> ConvertResult:
    """
    便捷函數：轉換單一文字

    Args:
        text: 輸入文字
        options: 轉換選項

    Returns:
        ConvertResult 物件
    """
    converter = get_converter(options)
    return converter.convert(text, options)
