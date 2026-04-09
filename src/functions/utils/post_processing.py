# post_processing.py
"""
Post-processing Module
- HTML Sanitizer, Content Filter, Risk Detection, Verbose Phrase Removal
"""

import bleach
import re

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


def post_process(llm_result, original_brief=None):
    # HTML Sanitizer
    safe_html = bleach.clean(
        llm_result.get("body_html", ""),
        tags=["p", "b", "i", "ul", "li", "br"],
        strip=True,
    )

    # Phase 14: 移除冗言
    safe_html = _remove_verbose_phrases(safe_html)

    # 風險檢測（在敏感詞過濾之前）
    all_text = safe_html + " " + llm_result.get("summary", "")
    if original_brief:
        all_text = original_brief + " " + all_text
    risk_alerts = _detect_risks(all_text)

    # Phase 14: 也移除 summary 中的冗言
    summary = llm_result.get("summary", "")
    if summary:
        summary = _remove_verbose_phrases(summary)

    # 敏感詞過濾
    llm_result["body_html"] = _filter_sensitive_text(safe_html)
    llm_result["summary"] = _filter_sensitive_text(summary)
    llm_result["tags"] = [
        _filter_sensitive_text(tag) for tag in llm_result.get("tags", [])
    ]

    # 設定風險警示
    llm_result["risk_alerts"] = risk_alerts

    return llm_result
