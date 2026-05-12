"""
品質檢查項目

在 LLM 生成結果之後、進後處理 Pipeline 之前，檢查內容品質。
每個檢查函數回傳 (passed: bool, reason: str)。
"""

import re
from typing import Tuple


def check_company_name(
    text: str, organ: str, title: str = "", summary: str = ""
) -> Tuple[bool, str]:
    """檢查內容是否包含公司名稱（檢查 body_html / title / summary 任一即可）

    由於寫作風格使用第一人稱（「我們」），body_html 可能不含公司名稱，
    因此放寬為 title 或 summary 有公司名即可。
    """
    if not text and not title and not summary:
        return False, "內容為空"
    if organ in text or organ in title or organ in summary:
        return True, ""
    return False, f"內容缺少公司名稱「{organ}」（檢查 body_html / title / summary）"


def check_min_length(text: str, threshold: int = 100) -> Tuple[bool, str]:
    """檢查內容長度"""
    text = text or ""
    length = len(text.strip())
    if length < threshold:
        return False, f"內容長度不足（{length} < {threshold}）"
    return True, ""


def check_no_truncation(text: str) -> Tuple[bool, str]:
    """檢查是否被截斷（以 ... 結尾）"""
    text = text or ""
    if text.rstrip().endswith("..."):
        return False, "內容結尾含有截斷符號「...」"
    return True, ""


def check_normal_start(text: str) -> Tuple[bool, str]:
    """檢查開頭是否為正常中文字元（非英文/數字/星號/符號開頭）"""
    text = text or ""
    stripped = text.strip()
    if not stripped:
        return False, "內容為空"
    # 移除 HTML 標籤後檢查
    clean = re.sub(r'<[^>]+>', '', stripped).strip()
    if not clean:
        return True, ""  # 純 HTML 結構不判定異常
    first_char = clean[0]
    # 英文/數字/星號/特殊符號開頭視為異常
    if re.match(r'[a-zA-Z0-9\*\[\（]', first_char):
        return False, f"內容開頭異常（首字元為「{first_char}」）"
    return True, ""


def check_no_artifact_markers(text: str) -> Tuple[bool, str]:
    """檢查是否包含 artifact 標記（**、【正確輸出】等）"""
    text = text or ""
    markers = [r'\*{2}', r'【正確輸出】', r'【例】']
    for marker in markers:
        if re.search(marker, text):
            return False, f"內容包含 artifact 標記「{marker}」"
    return True, ""


def check_no_repetition(text: str) -> Tuple[bool, str]:
    """檢查是否有重複的句子（LLM 陷入迴圈的常見現象）"""
    if not text:
        return True, ""
    # 以句號/驚嘆號/問號分割句子
    sentences = re.split(r'[。！？]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    seen = set()
    for s in sentences:
        if s in seen:
            return False, f"內容包含重複句子：「{s[:30]}...」"
        seen.add(s)
    return True, ""


def check_no_template_leftovers(text: str) -> Tuple[bool, str]:
    """檢查是否有未被替換的模板變數（如 {variable} 或 {{variable}}）"""
    if not text:
        return True, ""
    if re.search(r'\{[\w_]+\}', text) or re.search(r'\{\{[\w_]+\}\}', text):
        return False, "內容包含未被替換的模板變數"
    return True, ""


def check_chinese_ratio(text: str, threshold: float = 0.3) -> Tuple[bool, str]:
    """檢查中文字元比例是否過低（可能為非預期語言內容）"""
    text = text or ""
    clean = re.sub(r'<[^>]+>', '', text).strip()  # 移除 HTML 標籤
    if not clean:
        return False, "內容為空"
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean))
    total_chars = len(clean)
    ratio = chinese_chars / total_chars if total_chars > 0 else 0
    if ratio < threshold:
        return False, f"中文字元比例過低（{ratio:.0%} < {threshold:.0%}）"
    return True, ""
