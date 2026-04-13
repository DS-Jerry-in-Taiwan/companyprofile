"""
類型定義模組

定義 Taiwan Terms Converter 的資料類型和配置選項。
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class ConvertOptions:
    """轉換選項配置"""
    
    # 是否啟用 OpenCC 字符轉換
    enable_opencc: bool = True
    
    # 是否啟用詞彙對照替換
    enable_term_mapping: bool = True
    
    # 是否保留英文內容
    preserve_english: bool = True
    
    # 是否記錄轉換統計
    collect_stats: bool = True
    
    # 是否拋出錯誤或靜默處理
    raise_on_error: bool = False
    
    # 自訂詞庫路徑（優先於內建詞庫）
    custom_terms_path: Optional[str] = None
    
    # OpenCC 轉換模式
    opencc_mode: str = "s2twp"  # 簡體到台灣正體（含地區詞彙）
    
    # 效能相關選項
    precompile_regex: bool = True  # 預編譯正則表達式
    lazy_load: bool = True  # 懶加載詞庫


@dataclass  
class ConversionStats:
    """轉換統計資料"""
    
    # 輸入輸出統計
    input_length: int = 0
    output_length: int = 0
    
    # 轉換統計
    opencc_chars_converted: int = 0
    terms_replaced: int = 0
    terms_matched: List[str] = None  # 匹配到的詞彙列表
    
    # 效能統計（毫秒）
    loading_time_ms: float = 0.0
    opencc_time_ms: float = 0.0
    term_mapping_time_ms: float = 0.0
    total_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.terms_matched is None:
            self.terms_matched = []
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "input_length": self.input_length,
            "output_length": self.output_length,
            "opencc_chars_converted": self.opencc_chars_converted,
            "terms_replaced": self.terms_replaced,
            "terms_matched": self.terms_matched,
            "loading_time_ms": round(self.loading_time_ms, 2),
            "opencc_time_ms": round(self.opencc_time_ms, 2),
            "term_mapping_time_ms": round(self.term_mapping_time_ms, 2),
            "total_time_ms": round(self.total_time_ms, 2),
        }


@dataclass
class ConvertResult:
    """轉換結果"""
    
    # 主要輸出
    text: str = ""
    
    # 統計資訊
    stats: Optional[ConversionStats] = None
    
    # 錯誤資訊
    error: Optional[str] = None
    
    # 原始輸入（除錯用）
    original_text: Optional[str] = None
    
    def __post_init__(self):
        if self.stats is None:
            self.stats = ConversionStats()
    
    def success(self) -> bool:
        """轉換是否成功"""
        return self.error is None and self.text is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {
            "text": self.text,
            "success": self.success(),
            "error": self.error,
        }
        
        if self.stats:
            result["stats"] = self.stats.to_dict()
        
        return result


class ConversionError(Exception):
    """轉換錯誤"""
    pass