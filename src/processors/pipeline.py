"""
PostProcessPipeline - 後處理 Pipeline

依配置檔順序執行 Processor，支援啟停控制。
"""

import json
import os
import logging
from typing import List, Optional
from .base import Processor
from .registry import get_processor

logger = logging.getLogger(__name__)


class PostProcessPipeline:
    """後處理 Pipeline，依配置檔順序執行 Processor"""

    DEFAULT_CONFIG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config",
        "post_processing.json",
    )

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.processors: List[Processor] = []
        self._load_config()

    def _load_config(self):
        """讀取配置檔並建立 Processor 實例"""
        if not os.path.exists(self.config_path):
            logger.warning(f"Pipeline config not found: {self.config_path}")
            return

        with open(self.config_path, "r") as f:
            config = json.load(f)

        pipeline_config = config.get("pipeline", [])
        for item in pipeline_config:
            if not item.get("enabled", True):
                continue
            name = item["processor"]
            cls = get_processor(name)
            if cls is None:
                logger.warning(f"Processor not found: {name}")
                continue
            self.processors.append(cls())

        logger.info(f"Pipeline loaded: {[p.name for p in self.processors]}")

    def process(self, text: str) -> str:
        """依序執行所有 Processor"""
        for processor in self.processors:
            try:
                text = processor.process(text)
            except Exception as e:
                logger.error(f"Processor {processor.name} failed: {e}")
        return text

    def process_with_config(self, text: str, config: Optional[dict] = None) -> str:
        """依序執行所有 Processor，傳遞額外配置

        Args:
            text: 輸入文字
            config: 傳遞給每個 Processor 的額外配置 dict

        Returns:
            處理後文字
        """
        for processor in self.processors:
            try:
                text = processor.process(text, config=config)
            except Exception as e:
                logger.error(f"Processor {processor.name} failed: {e}")
        return text
