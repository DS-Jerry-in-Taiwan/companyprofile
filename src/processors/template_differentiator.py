"""
模板差異化 Processor

根據模板類型後處理內容（輕量驗證模式）。
"""

import logging
from typing import Optional, Any, Dict
from .base import Processor
from .registry import register

logger = logging.getLogger(__name__)

# 嘗試導入 template_differentiator
try:
    from src.functions.utils.template_differentiator import (
        differentiate_template as _differentiate_template,
    )

    TEMPLATE_DIFFERENTIATOR_AVAILABLE = True
except ImportError as e:
    TEMPLATE_DIFFERENTIATOR_AVAILABLE = False
    logger.warning(f"template_differentiator 模組未找到，跳過模板差異化處理: {e}")

    def _differentiate_template(html_content, template_type="standard", force_truncate=False):
        return html_content


class TemplateDifferentiatorProcessor(Processor):
    """模板差異化 Processor

    注意：此 Processor 需要 template_type 參數，透過 config dict 傳遞。
    例如：processor.process(text, config={"template_type": "brief"})
    """

    processor_name = "template_differentiator"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text:
            return text

        template_type = "standard"
        if config and isinstance(config, dict):
            template_type = config.get("template_type", "standard")

        try:
            from src.functions.utils.template_differentiator import (
                differentiate_template as _diff_tmpl,
            )

            return _diff_tmpl(text, template_type)
        except ImportError as e:
            logger.warning(f"template_differentiator 模組未找到，跳過模板差異化處理: {e}")
            return text


register(TemplateDifferentiatorProcessor)
