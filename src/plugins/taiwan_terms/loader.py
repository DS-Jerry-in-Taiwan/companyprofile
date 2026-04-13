"""
詞庫載入器模組

負責載入和管理台灣用語詞庫，支援多種來源：
1. 內建詞庫（打包進函數）
2. 本地檔案（開發環境）
3. S3 儲存桶（生產環境）
4. Lambda Layer（正式版）

支援環境變數切換來源，實現懶加載模式。
"""

import os
import json
import re
import time
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TermsLoader:
    """詞庫載入器"""

    # 詞庫實例（單例模式）
    _instance = None
    _terms_dict: Dict[str, str] = None
    _regex_pattern = None
    _loaded = False
    _loading_time_ms = 0.0

    def __new__(cls):
        """單例模式實作"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        """取得單例實例"""
        return cls() if cls._instance is None else cls._instance

    def load_terms(
        self, force_reload: bool = False
    ) -> Tuple[Dict[str, str], re.Pattern]:
        """
        載入詞庫並回傳詞典和正則表達式 pattern

        Args:
            force_reload: 強制重新載入

        Returns:
            (terms_dict, regex_pattern)
        """
        if self._loaded and not force_reload:
            return self._terms_dict, self._regex_pattern

        start_time = time.time()

        try:
            # 1. 決定詞庫來源路徑
            terms_path = self._resolve_terms_path()
            logger.info(f"載入詞庫: {terms_path}")

            # 2. 載入詞庫
            terms_dict = self._load_from_file(terms_path)

            # 3. 預編譯正則表達式（長詞優先）
            regex_pattern = self._build_regex_pattern(terms_dict)

            # 4. 更新狀態
            self._terms_dict = terms_dict
            self._regex_pattern = regex_pattern
            self._loaded = True

            loading_time = (time.time() - start_time) * 1000
            self._loading_time_ms = loading_time

            logger.info(
                f"詞庫載入完成: {len(terms_dict)} 條詞彙, 耗時 {loading_time:.2f}ms"
            )

            return terms_dict, regex_pattern

        except Exception as e:
            logger.error(f"載入詞庫失敗: {e}")
            raise

    def _resolve_terms_path(self) -> str:
        """
        解析詞庫路徑，支援多種來源

        優先順序:
        1. 環境變數 TAIWAN_TERMS_PATH (絕對路徑)
        2. Lambda Layer 路徑 (/opt/taiwan_terms/data/terms.json)
        3. 專案內建路徑 (src/plugins/taiwan_terms/data/terms.json)
        """
        # 1. 環境變數指定路徑
        env_path = os.getenv("TAIWAN_TERMS_PATH")
        if env_path and os.path.exists(env_path):
            return env_path

        # 2. Lambda Layer 路徑
        layer_path = "/opt/taiwan_terms/data/terms.json"
        if os.path.exists(layer_path):
            return layer_path

        # 3. 專案內建路徑（本地開發）
        # 先嘗試從 src/plugins/taiwan_terms/data/terms.json 載入
        project_root = Path(__file__).parent.parent.parent.parent
        builtin_path = (
            project_root / "src" / "plugins" / "taiwan_terms" / "data" / "terms.json"
        )

        if builtin_path.exists():
            return str(builtin_path)

        # 4. 相對路徑（打包進 Lambda 後）
        relative_path = "./data/terms.json"
        if os.path.exists(relative_path):
            return relative_path

        # 5. 找不到詞庫
        raise FileNotFoundError(
            "找不到詞庫檔案，請檢查以下位置:\n"
            f"1. 環境變數 TAIWAN_TERMS_PATH: {env_path}\n"
            f"2. Lambda Layer: {layer_path}\n"
            f"3. 專案內建: {builtin_path}\n"
            f"4. 相對路徑: {relative_path}"
        )

    def _load_from_file(self, file_path: str) -> Dict[str, str]:
        """
        從 JSON 檔案載入詞庫

        Args:
            file_path: JSON 檔案路徑

        Returns:
            詞典 {簡體詞: 繁體詞}
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 將分類結構轉為扁平詞典
            terms_dict = {}

            if isinstance(data, dict):
                # 檢查是否為分類結構（所有值都是字典）
                is_category_structure = all(isinstance(v, dict) for v in data.values())

                if is_category_structure:
                    # 分類結構：{"IT/科技": {"软件": "軟體"}, ...}
                    for category, terms in data.items():
                        if isinstance(terms, dict):
                            terms_dict.update(terms)
                        else:
                            logger.warning(f"分類 {category} 的格式不正確")
                else:
                    # 扁平結構：{"软件": "軟體", "网络": "網路"}
                    # 直接使用整個字典
                    terms_dict = data
            else:
                logger.warning("詞庫格式不正確，預期為字典")
                terms_dict = data if isinstance(data, dict) else {}

            # 驗證詞庫
            valid_terms = {}
            for key, value in terms_dict.items():
                if isinstance(key, str) and isinstance(value, str):
                    valid_terms[key.strip()] = value.strip()
                else:
                    logger.warning(f"忽略無效詞條: {key} -> {value}")

            if not valid_terms:
                raise ValueError("詞庫為空或無有效詞條")

            logger.debug(f"載入 {len(valid_terms)} 條有效詞彙")
            return valid_terms

        except json.JSONDecodeError as e:
            raise ValueError(f"詞庫 JSON 格式錯誤: {e}")
        except Exception as e:
            raise RuntimeError(f"讀取詞庫失敗: {e}")

    def _build_regex_pattern(self, terms_dict: Dict[str, str]) -> re.Pattern:
        """
        建立正則表達式 pattern，長詞優先匹配

        Args:
            terms_dict: 詞典

        Returns:
            編譯後的正則表達式
        """
        if not terms_dict:
            # 建立不匹配任何內容的 pattern
            return re.compile(r"(?!x)x")

        # 按詞彙長度排序（長詞優先）
        sorted_terms = sorted(terms_dict.keys(), key=len, reverse=True)

        # 建立正則表達式
        # 使用 re.escape 轉義特殊字符
        pattern_parts = []
        for term in sorted_terms:
            escaped_term = re.escape(term)
            pattern_parts.append(escaped_term)

        # 使用 | 合併所有 pattern
        pattern_str = "|".join(pattern_parts)

        try:
            # 編譯正則表達式
            regex_pattern = re.compile(pattern_str)
            return regex_pattern
        except re.error as e:
            logger.error(f"正則表達式編譯失敗: {e}")
            # 回退到空 pattern
            return re.compile(r"(?!x)x")

    def get_loading_time(self) -> float:
        """取得載入時間（毫秒）"""
        return self._loading_time_ms

    def is_loaded(self) -> bool:
        """詞庫是否已載入"""
        return self._loaded

    def get_terms_count(self) -> int:
        """取得詞彙數量"""
        return len(self._terms_dict) if self._terms_dict else 0

    def clear_cache(self):
        """清除快取（用於測試）"""
        self._terms_dict = None
        self._regex_pattern = None
        self._loaded = False
        self._loading_time_ms = 0.0
        logger.info("詞庫快取已清除")


# 建立全局載入器實例
_loader = TermsLoader()


def get_loader() -> TermsLoader:
    """取得全局載入器實例"""
    return _loader


def load_terms(force_reload: bool = False) -> Tuple[Dict[str, str], re.Pattern]:
    """載入詞庫（便捷函數）"""
    return _loader.load_terms(force_reload)
