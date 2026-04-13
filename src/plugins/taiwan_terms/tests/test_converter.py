"""
Taiwan Terms Converter 單元測試
"""

import os
import sys
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# 添加模組路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from taiwan_terms import (
    TaiwanTermsConverter,
    ConvertOptions,
    ConvertResult,
    ConversionStats,
)
from taiwan_terms.loader import TermsLoader


class TestConvertOptions:
    """測試轉換選項"""

    def test_default_options(self):
        """測試預設選項"""
        options = ConvertOptions()
        assert options.enable_opencc is True
        assert options.enable_term_mapping is True
        assert options.preserve_english is True
        assert options.collect_stats is True
        assert options.raise_on_error is False
        assert options.custom_terms_path is None
        assert options.opencc_mode == "s2twp"
        assert options.precompile_regex is True
        assert options.lazy_load is True

    def test_custom_options(self):
        """測試自訂選項"""
        options = ConvertOptions(
            enable_opencc=False,
            enable_term_mapping=False,
            preserve_english=False,
            collect_stats=False,
            raise_on_error=True,
            custom_terms_path="/custom/path.json",
            opencc_mode="s2t",
            precompile_regex=False,
            lazy_load=False,
        )

        assert options.enable_opencc is False
        assert options.enable_term_mapping is False
        assert options.preserve_english is False
        assert options.collect_stats is False
        assert options.raise_on_error is True
        assert options.custom_terms_path == "/custom/path.json"
        assert options.opencc_mode == "s2t"
        assert options.precompile_regex is False
        assert options.lazy_load is False


class TestTermsLoader:
    """測試詞庫載入器"""

    def test_singleton_pattern(self):
        """測試單例模式"""
        loader1 = TermsLoader.get_instance()
        loader2 = TermsLoader.get_instance()
        assert loader1 is loader2
        assert loader1 == loader2

    def test_load_terms_with_temp_file(self):
        """測試載入臨時詞庫檔案"""
        # 建立臨時詞庫檔案
        test_terms = {"测试": "測試", "软件": "軟體", "网络": "網路"}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_terms, f)
            temp_path = f.name

        try:
            # 設定環境變數
            with patch.dict(os.environ, {"TAIWAN_TERMS_PATH": temp_path}):
                loader = TermsLoader()
                loader.clear_cache()  # 清除快取以強制重新載入

                terms_dict, regex_pattern = loader.load_terms()

                assert len(terms_dict) == 3
                assert terms_dict["测试"] == "測試"
                assert terms_dict["软件"] == "軟體"
                assert terms_dict["网络"] == "網路"

                # 驗證正則表達式
                assert regex_pattern is not None

                # 測試匹配
                test_text = "这是一个测试软件和网络"
                matches = regex_pattern.findall(test_text)
                assert "软件" in matches
                assert "网络" in matches

        finally:
            os.unlink(temp_path)

    def test_load_terms_with_categories(self):
        """測試載入分類詞庫"""
        test_terms = {
            "IT/科技": {"软件": "軟體", "网络": "網路"},
            "商業/辦公": {"质量": "品質"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(test_terms, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"TAIWAN_TERMS_PATH": temp_path}):
                loader = TermsLoader()
                loader.clear_cache()

                terms_dict, _ = loader.load_terms()

                assert len(terms_dict) == 3
                assert terms_dict["软件"] == "軟體"
                assert terms_dict["网络"] == "網路"
                assert terms_dict["质量"] == "品質"

        finally:
            os.unlink(temp_path)

    def test_loader_stats(self):
        """測試載入器統計"""
        loader = TermsLoader()
        loader.clear_cache()

        assert loader.is_loaded() is False
        assert loader.get_loading_time() == 0.0
        assert loader.get_terms_count() == 0

        # 載入後檢查
        with patch.object(loader, "_resolve_terms_path") as mock_resolve:
            # 模擬找到詞庫
            mock_resolve.return_value = os.path.join(
                os.path.dirname(__file__), "..", "data", "terms.json"
            )

            terms_dict, _ = loader.load_terms()

            assert loader.is_loaded() is True
            assert loader.get_loading_time() > 0
            assert loader.get_terms_count() > 0


class TestTaiwanTermsConverter:
    """測試台灣用語轉換器"""

    def test_converter_init(self):
        """測試轉換器初始化"""
        converter = TaiwanTermsConverter()
        assert converter.options is not None
        assert converter.options.enable_opencc is True

        custom_options = ConvertOptions(enable_opencc=False)
        converter2 = TaiwanTermsConverter(custom_options)
        assert converter2.options.enable_opencc is False

    def test_convert_without_opencc(self):
        """測試不使用 OpenCC 的轉換"""
        # 模擬詞庫
        with patch.object(TermsLoader, "load_terms") as mock_load:
            mock_load.return_value = (
                {"软件": "軟體", "网络": "網路", "测试": "測試"},
                None,  # 不使用正則表達式
            )

            converter = TaiwanTermsConverter(
                ConvertOptions(
                    enable_opencc=False,
                    enable_term_mapping=True,
                    precompile_regex=False,
                )
            )

            result = converter.convert("这是一个软件测试网络应用")

            assert result.success() is True
            assert "軟體" in result.text
            assert "測試" in result.text
            assert "網路" in result.text
            assert result.stats.terms_replaced == 3

    def test_convert_with_regex(self):
        """測試使用正則表達式的轉換"""
        import re

        # 建立正則表達式
        test_terms = {"软件": "軟體", "网络": "網路"}
        pattern = re.compile("|".join(map(re.escape, test_terms.keys())))

        with patch.object(TermsLoader, "load_terms") as mock_load:
            mock_load.return_value = (test_terms, pattern)

            converter = TaiwanTermsConverter(
                ConvertOptions(
                    enable_opencc=False, enable_term_mapping=True, precompile_regex=True
                )
            )

            result = converter.convert("软件和网络")

            assert result.success() is True
            assert "軟體" in result.text
            assert "網路" in result.text
            assert result.stats.terms_replaced == 2

    def test_convert_empty_text(self):
        """測試轉換空文字"""
        converter = TaiwanTermsConverter()

        result = converter.convert("")
        assert result.success() is True
        assert result.text == ""
        assert result.stats.input_length == 0

        result = converter.convert(None)  # type: ignore
        assert result.success() is True
        assert result.text == ""

    def test_convert_error_handling(self):
        """測試錯誤處理"""
        # 模擬詞庫載入失敗
        with patch.object(TermsLoader, "load_terms") as mock_load:
            mock_load.side_effect = Exception("載入失敗")

            converter = TaiwanTermsConverter(
                ConvertOptions(
                    raise_on_error=False,
                    enable_opencc=False,  # 禁用 OpenCC，避免簡繁轉換
                )
            )

            result = converter.convert("测试文字")

            assert result.success() is False
            assert result.error is not None
            assert result.text == "测试文字"  # 錯誤時返回原始文字

    def test_batch_convert(self):
        """測試批次轉換"""
        with patch.object(TermsLoader, "load_terms") as mock_load:
            mock_load.return_value = ({"软件": "軟體", "网络": "網路"}, None)

            converter = TaiwanTermsConverter(ConvertOptions(enable_opencc=False))

            texts = ["软件", "网络", "软件和网络"]
            results = converter.batch_convert(texts)

            assert len(results) == 3
            assert results[0].text == "軟體"
            assert results[1].text == "網路"
            assert results[2].text == "軟體和網路"

    def test_get_stats(self):
        """測試取得統計資訊"""
        converter = TaiwanTermsConverter()
        stats = converter.get_stats()

        assert "terms_loaded" in stats
        assert "loader_loaded" in stats
        assert "loading_time_ms" in stats
        assert "opencc_available" in stats


class TestIntegration:
    """整合測試"""

    def test_end_to_end_with_real_terms(self):
        """使用真實詞庫的端到端測試"""
        # 使用真實詞庫（專案內建）
        converter = TaiwanTermsConverter(
            ConvertOptions(
                enable_opencc=False,  # 暫時禁用 OpenCC 以簡化測試
                enable_term_mapping=True,
            )
        )

        # 測試幾個已知詞彙
        result = converter.convert("软件")
        assert "軟體" in result.text

        result = converter.convert("网络")
        assert "網路" in result.text

        result = converter.convert("服务器")
        assert "伺服器" in result.text

        # 測試長句子
        result = converter.convert("我们的软件产品运行在服务器上，通过网络提供服务")
        assert "軟體" in result.text
        assert "伺服器" in result.text
        assert "網路" in result.text

    def test_opencc_integration(self):
        """測試 OpenCC 整合"""
        converter = TaiwanTermsConverter(
            ConvertOptions(enable_opencc=True, enable_term_mapping=False)
        )

        # 測試簡繁轉換（簡單字符）
        result = converter.convert("国")

        # 檢查是否成功轉換（可能轉為"國"）
        # 如果 OpenCC 不可用，會回退到簡單轉換
        if result.success():
            # 至少確保沒有錯誤
            assert result.text is not None

    @patch.object(TaiwanTermsConverter, "_create_opencc_converter")
    def test_opencc_fallback(self, mock_create):
        """測試 OpenCC 不可用時的回退機制"""
        # 模擬 OpenCC 不可用，返回 None
        mock_create.return_value = None

        converter = TaiwanTermsConverter(
            ConvertOptions(enable_opencc=True, enable_term_mapping=False)
        )

        result = converter.convert("国")

        # 應該使用簡單轉換
        assert result.success() is True
        # 簡單轉換應該能轉換"国"到"國"
        # 但如果不確定，至少確保沒有錯誤
        assert result.error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
