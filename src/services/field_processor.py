"""
欄位處理虛擬層

由 config/field_processing.json 驅動，自動處理 request 欄位：
- 過濾控制欄位（organ, mode 等），不進 prompt
- 格式化數值欄位（資本額加「萬元」、員工人數加「人」等）
- 產生 prompt 用的字串列表（只取 config 定義的欄位，防止 LLM 飄移）

使用方式：
    processor = FieldProcessor()
    user_input = processor.process(request_data)
    prompt_items = processor.get_prompt_items(user_input)
"""

import json
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


class FieldProcessor:
    """欄位處理器：config 驅動的動態欄位處理"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str = None) -> dict:
        """讀取 field_processing.json，失敗時回傳空配置"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config", "field_processing.json"
            )
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"無法載入 field_processing config: {e}")
            return {"control_fields": [], "fields": {}}

    def process(self, raw_data: dict) -> dict:
        """① 前處理：過濾控制欄位、格式化數值

        不在 control_fields 且非 None 的欄位都會被保留，
        供 DB 儲存使用。

        Args:
            raw_data: API 請求的原始 dict

        Returns:
            處理後的 user_input dict（含格式化後的公司資訊欄位）
        """
        control_set = set(self.config.get("control_fields", []))
        field_defs = self.config.get("fields", {})
        result = {}

        for key, value in raw_data.items():
            # 跳過控制欄位（不進 user_input）
            if key in control_set:
                continue
            if value is None:
                continue

            # 有定義格式規則 → 套用格式化
            if key in field_defs:
                result[key] = self._format_field(key, value, field_defs[key])
            else:
                # 未知欄位 → 原樣保留（可用於 DB 儲存，但不進 prompt）
                result[key] = value

        return result

    def get_prompt_items(self, processed: dict) -> list:
        """② 產生 prompt 用的字串列表（只取 config 定義的欄位）

        不在 config 的欄位（如前端追蹤參數 utm_source）不會進 prompt，
        防止 LLM 飄移。

        Args:
            processed: process() 回傳的 dict

        Returns:
            字串列表，每個元素是一行資訊，如 "[資本額]: 1000 萬元"
        """
        field_defs = self.config.get("fields", {})
        items = []

        for key, value in processed.items():
            # 不在 config 的欄位不進 prompt
            if key not in field_defs:
                continue
            # 空值跳過
            if value is None or value == "" or value == []:
                continue
            label = field_defs[key]["label"]
            items.append(f"[{label}]: {value}")

        return items

    def _format_field(self, key: str, value: Any, rule: dict) -> str:
        """根據 config 規則格式化單一欄位"""
        field_type = rule.get("type", "string")

        # array 型別（如 brand_names）→ join
        if field_type == "array" and isinstance(value, list):
            value = "、".join(str(v) for v in value)

        # number 型別（如 capital）→ 轉 float
        if field_type == "number":
            try:
                value = float(value)
            except (TypeError, ValueError):
                pass

        # 套用 format 模板
        fmt = rule.get("format", "{value}")
        return fmt.format(value=value)
