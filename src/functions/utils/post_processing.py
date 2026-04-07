# post_processing.py
"""
Post-processing Module
- HTML Sanitizer, Content Filter, Risk Detection
"""

import bleach

SENSITIVE_WORDS = ["賭博", "情色"]
RISK_WORDS = ["歧視", "仇恨", "暴力", "未成年", "色情", "赌博", "情色"]


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


def post_process(llm_result, original_brief=None):
    # HTML Sanitizer
    safe_html = bleach.clean(
        llm_result.get("body_html", ""),
        tags=["p", "b", "i", "ul", "li", "br"],
        strip=True,
    )

    # 風險檢測（在敏感詞過濾之前）
    all_text = llm_result.get("body_html", "") + " " + llm_result.get("summary", "")
    if original_brief:
        all_text = original_brief + " " + all_text
    risk_alerts = _detect_risks(all_text)

    # 敏感詞過濾
    llm_result["body_html"] = _filter_sensitive_text(safe_html)
    llm_result["summary"] = _filter_sensitive_text(llm_result.get("summary", ""))
    llm_result["tags"] = [
        _filter_sensitive_text(tag) for tag in llm_result.get("tags", [])
    ]

    # 設定風險警示
    llm_result["risk_alerts"] = risk_alerts

    return llm_result
