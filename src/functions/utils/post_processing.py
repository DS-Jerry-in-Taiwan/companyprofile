# post_processing.py
"""
Post-processing Module
- HTML Sanitizer, Content Filter, Risk Detection, Verbose Phrase Removal
- Phase 14.1: Taiwan Terms Conversion (Chinese Mainland to Taiwan terminology)
"""

import bleach
import re
import logging

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
    print(f"警告: 台灣用語轉換器不可用 - {e}")

SENSITIVE_WORDS = ["賭博", "情色"]
RISK_WORDS = ["歧視", "仇恨", "暴力", "未成年", "色情", "赌博", "情色"]

# Phase 14: 常見冗言模式列表
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

# Phase 14 Agent F/G: 格式統一相關函數


def _normalize_format(text):
    """
    統一文本格式（標點、空格、換行）

    Args:
        text: 輸入文本（可包含 HTML）

    Returns:
        格式統一後的文本
    """
    if not text:
        return text

    # 檢查是否包含 HTML 標籤
    has_html = "<" in text and ">" in text

    if has_html:
        return _normalize_html_format(text)
    else:
        return _normalize_plain_text_format(text)


def _normalize_html_format(text):
    """
    統一 HTML 內容的格式

    處理邏輯:
    1. 使用 BeautifulSoup 解析 HTML
    2. 遍歷所有文本節點
    3. 對每個文本節點應用格式統一
    4. 保持 HTML 標籤結構完整
    5. 處理標籤之間的換行
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(text, "html.parser")

    for tag in soup.find_all(True):
        if tag.string:
            normalized = _normalize_plain_text_format(tag.string)
            tag.string = normalized

    # 將 BeautifulSoup 對象轉換為字符串
    result = str(soup)

    # 處理 HTML 標籤之間的換行
    result = _normalize_line_breaks(result)

    return result


def _normalize_plain_text_format(text):
    """
    統一純文本格式

    處理順序:
    1. 統一標點符號
    2. 移除多餘空格
    3. 統一換行格式
    """
    text = _normalize_punctuation(text)
    text = _remove_extra_spaces(text)
    text = _normalize_line_breaks(text)
    return text


def _normalize_punctuation(text):
    """
    統一標點符號為中文標點

    轉換規則:
    - , → ，
    - . → 。 (句尾)
    - ! → ！
    - ? → ？
    - : → ：
    - ; → ；
    - " → 「」
    - ' → 『』
    - ( → （
    - ) → ）

    例外:
    - 英文單詞內部的標點不轉換
    - 數字中的小數點不轉換 (如 3.14)
    - 網址中的標點不轉換
    """
    import re

    # 定義標點轉換映射
    punct_map = {
        ",": "，",
        "!": "！",
        "?": "？",
        ":": "：",
        ";": "；",
        "(": "（",
        ")": "）",
        "[": "［",
        "]": "］",
    }

    result = []
    i = 0
    while i < len(text):
        char = text[i]

        # 處理英文句點
        if char == ".":
            if (
                i > 0
                and i < len(text) - 1
                and text[i - 1].isdigit()
                and text[i + 1].isdigit()
            ):
                result.append(char)  # 小數點保留
            elif i > 0 and text[i - 1 : i + 4] in ["http", "www."]:
                result.append(char)  # 網址保留
            elif i == len(text) - 1 or text[i + 1] in " \n\t":
                result.append("。")  # 句尾句號
            else:
                result.append(char)
        # 處理引號 - 需要配對處理
        elif char == '"':
            # 簡單處理：檢查前後文來決定是左引號還是右引號
            # 這裡簡化為都轉換為「
            result.append("「")
        elif char == "'":
            result.append("『")
        # 處理URL中的冒號不轉換
        elif char == ":" and i > 0:
            # 檢查是否是URL的一部分
            if i >= 4 and text[i - 4 : i] == "http":
                result.append(":")  # URL中的冒號保留
            elif i >= 3 and text[i - 3 : i] == "ftp":
                result.append(":")  # FTP URL中的冒號保留
            else:
                result.append("：")
        elif char in punct_map:
            result.append(punct_map[char])
        else:
            result.append(char)

        i += 1

    return "".join(result)


def _remove_extra_spaces(text):
    """
    移除多餘空格

    處理規則:
    1. 連續多個空格 → 單個空格
    2. 全角空格 → 半角空格
    3. 標點後的多餘空格 → 移除
    4. 段落首尾空格 → 移除
    """
    import re

    text = text.strip()
    text = text.replace("　", " ")
    text = re.sub(r" +", " ", text)
    # 移除標點前後的空格
    text = re.sub(r"\s+([，。！？；：])", r"\1", text)
    text = re.sub(r"([，。！？；：])\s+", r"\1", text)

    return text


def _normalize_line_breaks(text):
    """
    統一換行格式

    處理規則:
    1. 連續 3 個及以上換行 → 2 個換行
    2. 保持段落間 1-2 個換行
    3. 移除段落開頭和結尾的多餘換行
    """
    import re

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip("\n")

    return text


def _filter_sensitive_text(text):
    filtered = text or ""
    for word in SENSITIVE_WORDS:
        filtered = filtered.replace(word, "***")
    return filtered


def _detect_risks(text):
    """檢測高風險字眼"""
    risks = []
    text = text or ""
    text_lower = text.lower()
    for word in RISK_WORDS:
        if word in text_lower:
            risks.append(f"包含可能高風險字眼: {word}")
    return risks


def _remove_verbose_phrases(text):
    """移除常見的冗言開頭"""
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
            # 移除匹配的模式
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

        # 移除常見的開頭標點和空白
        text = re.sub(r"^[:：,\s]+", "", text).strip()

    return text


def _convert_to_taiwan_terms(text):
    """
    將文字中的中國用語轉換為台灣用語

    Args:
        text: 輸入文字（可包含HTML）

    Returns:
        轉換後文字
    """
    if not text or not TAIWAN_TERMS_AVAILABLE:
        return text

    text = text.strip()
    if not text:
        return text

    # 檢查是否包含 HTML 標籤
    has_html = "<" in text and ">" in text

    if has_html:
        # 使用 BeautifulSoup 處理 HTML
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(text, "html.parser")

        # 遍歷所有標籤
        for tag in soup.find_all(True):
            if tag.string:
                # 轉換文本內容
                original_text = tag.string.strip()
                if original_text:
                    # 使用台灣用語轉換器
                    converter = get_taiwan_converter()
                    result = converter.convert(original_text)
                    if result.success():
                        tag.string = result.text
                    else:
                        # 轉換失敗，保留原始文字
                        logger.warning(f"台灣用語轉換失敗: {result.error}")
                        tag.string = original_text

        return str(soup)
    else:
        # 純文本處理
        converter = get_taiwan_converter()
        result = converter.convert(text)
        if result.success():
            return result.text
        else:
            logger.warning(f"台灣用語轉換失敗: {result.error}")
            return text


def post_process(llm_result, original_brief=None, template_type="standard"):
    # HTML Sanitizer
    body_html = llm_result.get("body_html", "")
    if body_html is None:
        body_html = ""

    safe_html = bleach.clean(
        body_html,
        tags=["p", "b", "i", "ul", "li", "br"],
        strip=True,
    )

    # Phase 14: 移除冗言
    safe_html = _remove_verbose_phrases(safe_html)

    # Phase 14.1: 台灣用語轉換
    if TAIWAN_TERMS_AVAILABLE:
        safe_html = _convert_to_taiwan_terms(safe_html)
        logger.info("已應用台灣用語轉換到 body_html")
    else:
        logger.warning("台灣用語轉換器不可用，跳過轉換")

    # Phase 14 Agent F/G: 格式統一 (新增)
    safe_html = _normalize_format(safe_html)
    logger.info("已應用格式統一到 body_html")

    # Phase 14 Agent F/G: 內容多樣化 (新增)
    try:
        from src.functions.utils.content_diversifier import diversify_content

        safe_html = diversify_content(safe_html)
        logger.info("已應用內容多樣化到 body_html")
    except ImportError as e:
        logger.warning(f"content_diversifier 模組未找到，跳過多樣化處理: {e}")

    # Phase 14 Agent F/G: 模板差異化 (新增)
    try:
        from src.functions.utils.template_differentiator import differentiate_template

        safe_html = differentiate_template(safe_html, template_type)
        logger.info(f"已應用模板差異化到 body_html (模板類型: {template_type})")
    except ImportError as e:
        logger.warning(f"template_differentiator 模組未找到，跳過模板差異化處理: {e}")

    # 風險檢測（在敏感詞過濾之前）
    summary = llm_result.get("summary", "")
    if summary is None:
        summary = ""
    all_text = safe_html + " " + summary
    if original_brief:
        all_text = original_brief + " " + all_text
    risk_alerts = _detect_risks(all_text)

    # Phase 14: 也移除 summary 中的冗言
    summary = llm_result.get("summary", "")
    if summary:
        summary = _remove_verbose_phrases(summary)

    # Phase 14.1: 台灣用語轉換 (summary)
    if TAIWAN_TERMS_AVAILABLE and summary:
        summary = _convert_to_taiwan_terms(summary)
        logger.info("已應用台灣用語轉換到 summary")

    # Phase 14 Agent F/G: 格式統一 (summary)
    if summary:
        summary = _normalize_format(summary)
        logger.info("已應用格式統一到 summary")

    # Phase 14 Agent F/G: 內容多樣化 (summary)
    if summary:
        try:
            from src.functions.utils.content_diversifier import diversify_content

            summary = diversify_content(summary)
            logger.info("已應用內容多樣化到 summary")
        except ImportError as e:
            logger.warning(
                f"content_diversifier 模組未找到，跳過 summary 多樣化處理: {e}"
            )

    # Phase 14 Agent F/G: 模板差異化 (summary)
    if summary:
        try:
            from src.functions.utils.template_differentiator import (
                differentiate_template,
            )

            summary = differentiate_template(summary, template_type)
            logger.info(f"已應用模板差異化到 summary (模板類型: {template_type})")
        except ImportError as e:
            logger.warning(
                f"template_differentiator 模組未找到，跳過 summary 模板差異化處理: {e}"
            )

    # Phase 14.1: 台灣用語轉換 (tags)
    tags = llm_result.get("tags", [])
    if tags is None:
        tags = []
    if TAIWAN_TERMS_AVAILABLE and tags:
        converted_tags = []
        for tag in tags:
            if tag and isinstance(tag, str):
                converted_tag = _convert_to_taiwan_terms(tag)
                converted_tags.append(converted_tag)
            else:
                converted_tags.append(tag)
        tags = converted_tags
        logger.info(f"已應用台灣用語轉換到 {len(tags)} 個 tags")

    # 敏感詞過濾
    llm_result["body_html"] = _filter_sensitive_text(safe_html)
    llm_result["summary"] = _filter_sensitive_text(summary)
    llm_result["tags"] = [_filter_sensitive_text(tag) for tag in tags]

    # 設定風險警示
    llm_result["risk_alerts"] = risk_alerts

    return llm_result
