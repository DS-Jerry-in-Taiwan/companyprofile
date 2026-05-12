"""
冗言移除 Processor

移除常見的冗言開頭（如下：「以下是生成的內容：」「根據您的要求，」等）。
"""

import re
from typing import Optional
from .base import Processor
from .registry import register

# 常見冗言模式列表（與 post_processing.py 一致）
VERBOSE_PATTERNS = [
    # 英文冗言
    r"^以下是.*?:",
    r"^Here is.*?:",
    r"^Based on.*?:",
    # 中文冗言
    r"^以下是生成的內容",
    r"^以下是生成的簡介",
    r"^以下是公司簡介",
    r"^以下是優化結果",
    r"^以下是優化後的簡介",
    r"^根據您的要求",
    r"^根據以上資訊[，,]",
    r"^根據提供的信息[，,]",
    r"^根據您提供的資料[，,]",
    r"^根據公司資訊[，,]",
    r"^根據資料顯示[，,]",
    r"^以下是公司簡介的優化版本",
    r"^優化後的內容如下",
    r"^生成結果如下",
    r"^以下是生成的摘要",
]


class VerboseRemoverProcessor(Processor):
    """冗言移除 Processor"""

    processor_name = "verbose_remover"

    def process(self, text: str, config: Optional[dict] = None) -> str:
        if not text:
            return text

        text = text.strip()

        # 檢查是否包含 HTML 標籤
        has_html = "<" in text and ">" in text

        if has_html:
            # 使用 BeautifulSoup 處理 HTML
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(text, "html.parser")

            # 遍歷所有標籤
            for tag in soup.find_all(True):
                if tag.string:
                    # 移除冗言
                    cleaned = tag.string.strip()
                    for pattern in VERBOSE_PATTERNS:
                        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
                    # 移除開頭標點
                    cleaned = re.sub(r"^[:：,\s]+", "", cleaned).strip()
                    tag.string = cleaned

            return str(soup)
        else:
            # 純文本處理
            for pattern in VERBOSE_PATTERNS:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

            # 移除常見的開頭標點和空白
            text = re.sub(r"^[:：,\s]+", "", text).strip()

        return text


register(VerboseRemoverProcessor)
