"""
配置載入器模組（Phase20 配置驅動架構）

提供載入和驗證 field_mapping.json 的功能
"""

import json
import logging
import os
from typing import Dict, List

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置路徑
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "config")
FIELD_MAPPING_PATH = os.path.join(CONFIG_DIR, "field_mapping.json")
FIELD_MAPPING_SCHEMA_PATH = os.path.join(CONFIG_DIR, "field_mapping_schema.json")

# 預設映射（fallback 用）
DEFAULT_FIELD_MAPPING = {
    "fields": [
        "unified_number",
        "capital",
        "founded_date",
        "address",
        "officer",
        "main_services",
        "business_items"
    ],
    "mapping": {
        "unified_number": "foundation",
        "capital": "foundation",
        "founded_date": "foundation",
        "address": "foundation",
        "officer": "foundation",
        "main_services": "core",
        "business_items": "core"
    },
    "aspects": ["foundation", "core", "vibe", "future"]
}

# 快取
_config_cache = None


def _validate_config(config: Dict) -> bool:
    """
    驗證配置格式是否正確
    
    使用簡單的 key 檢查，避免依賴 jsonschema 套件
    """
    required_keys = ["fields", "mapping", "aspects"]
    
    # 檢查必要 key
    for key in required_keys:
        if key not in config:
            logger.warning(f"配置缺少必要欄位: {key}")
            return False
    
    # 檢查 fields
    if not isinstance(config.get("fields"), list) or len(config["fields"]) == 0:
        logger.warning("fields 必須是非空列表")
        return False
    
    # 檢查 mapping
    if not isinstance(config.get("mapping"), dict) or len(config["mapping"]) == 0:
        logger.warning("mapping 必須是非空字典")
        return False
    
    # 檢查 aspects
    valid_aspects = ["foundation", "core", "vibe", "future"]
    if not isinstance(config.get("aspects"), list):
        logger.warning("aspects 必須是列表")
        return False
    
    # 檢查映射值是否有效
    for field, aspect in config.get("mapping", {}).items():
        if aspect not in valid_aspects:
            logger.warning(f"映射值無效: {field} -> {aspect}")
            return False
    
    return True


def load_field_mapping() -> Dict:
    """
    載入並驗證 field_mapping.json
    
    Returns:
        Dict: 配置字典，驗證失敗回傳預設值
    """
    global _config_cache
    
    # 如果已經快取，直接回傳
    if _config_cache is not None:
        return _config_cache
    
    # 檢查檔案是否存在
    if not os.path.exists(FIELD_MAPPING_PATH):
        logger.warning(f"配置文件不存在: {FIELD_MAPPING_PATH}，使用預設值")
        _config_cache = DEFAULT_FIELD_MAPPING.copy()
        return _config_cache
    
    # 嘗試讀取 JSON
    try:
        with open(FIELD_MAPPING_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"配置文件格式錯誤: {e}，使用預設值")
        _config_cache = DEFAULT_FIELD_MAPPING.copy()
        return _config_cache
    except Exception as e:
        logger.warning(f"讀取配置文件失敗: {e}，使用預設值")
        _config_cache = DEFAULT_FIELD_MAPPING.copy()
        return _config_cache
    
    # 驗證配置格式
    if not _validate_config(config):
        logger.warning("配置驗證失敗，使用預設值")
        _config_cache = DEFAULT_FIELD_MAPPING.copy()
        return _config_cache
    
    # 驗證通過，快取並回傳
    _config_cache = config
    logger.info("配置載入成功")
    return _config_cache


def get_fields() -> List[str]:
    """
    取得字段列表
    
    Returns:
        List[str]: 字段名稱列表
    """
    config = load_field_mapping()
    return config.get("fields", DEFAULT_FIELD_MAPPING["fields"])


def get_field_to_aspect_mapping() -> Dict:
    """
    取得字段 → 面向映射
    
    Returns:
        Dict: {字段名: 面向名} 的映射字典
    """
    config = load_field_mapping()
    return config.get("mapping", DEFAULT_FIELD_MAPPING["mapping"])


def get_aspects() -> List[str]:
    """
    取得面向列表
    
    Returns:
        List[str]: 面向名稱列表
    """
    config = load_field_mapping()
    return config.get("aspects", DEFAULT_FIELD_MAPPING["aspects"])


def get_aspect_to_fields_mapping() -> Dict[str, List[str]]:
    """
    取得面向 → 字段列表的反向映射
    
    Returns:
        Dict: {面向名: [字段列表]}
    """
    field_to_aspect = get_field_to_aspect_mapping()
    aspect_to_fields = {}
    
    for field, aspect in field_to_aspect.items():
        if aspect not in aspect_to_fields:
            aspect_to_fields[aspect] = []
        aspect_to_fields[aspect].append(field)
    
    return aspect_to_fields


def reload_config() -> None:
    """
    重新載入配置（清除快取）
    
    用於測試或配置更新後強制重新讀取
    """
    global _config_cache
    _config_cache = None
    logger.info("已清除配置快取")


def clear_cache() -> None:
    """清除配置快取的別名"""
    reload_config()
