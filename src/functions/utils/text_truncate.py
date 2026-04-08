"""
文字截斷工具模組
用於確保文本內容符合字數限制
"""

import re
from bs4 import BeautifulSoup


def count_chinese_characters(text: str) -> int:
    """
    計算文本中的中文字數

    Args:
        text: 要計算的文本

    Returns:
        int: 中文字符數量
    """
    # 移除 HTML 標籤
    clean_text = BeautifulSoup(text, "html.parser").get_text()
    # 計算所有字符（包含中英文、數字、標點符號）
    return len(clean_text)


def truncate_text(text: str, word_limit: int, preserve_html: bool = True) -> str:
    """
    截斷文本至指定字數

    Args:
        text: 要截斷的文本
        word_limit: 字數限制
        preserve_html: 是否保留 HTML 標籤

    Returns:
        str: 截斷後的文本
    """
    if not text or not word_limit:
        return text

    current_length = count_chinese_characters(text)

    # 如果未超過限制，直接返回
    if current_length <= word_limit:
        return text

    if preserve_html:
        return _truncate_html(text, word_limit)
    else:
        return text[:word_limit]


def _truncate_html(html_text: str, word_limit: int) -> str:
    """
    截斷 HTML 文本，保持標籤完整性

    Args:
        html_text: HTML 格式的文本
        word_limit: 字數限制

    Returns:
        str: 截斷後的 HTML 文本
    """
    soup = BeautifulSoup(html_text, "html.parser")
    plain_text = soup.get_text()

    # 如果純文本已經在限制內
    if len(plain_text) <= word_limit:
        return html_text

    # 簡單策略：截斷純文本，然後重新包裝在 <p> 標籤中
    truncated_text = plain_text[:word_limit]

    # 嘗試在最近的句號、逗號或空格處截斷
    for delimiter in ["。", "！", "？", "，", "、", " "]:
        last_pos = truncated_text.rfind(delimiter)
        if last_pos > word_limit * 0.8:  # 至少保留 80% 的內容
            truncated_text = truncated_text[: last_pos + 1]
            break

    # 重新包裝
    return f"<p>{truncated_text}</p>"


def truncate_llm_output(output: dict, word_limit: int) -> dict:
    """
    截斷 LLM 輸出的所有相關欄位

    Args:
        output: LLM 輸出字典，包含 title, body_html, summary 等
        word_limit: 字數限制

    Returns:
        dict: 截斷後的輸出
    """
    if not word_limit:
        return output

    result = output.copy()

    # 截斷 body_html（主要內容）
    if "body_html" in result and result["body_html"]:
        result["body_html"] = truncate_text(
            result["body_html"], word_limit, preserve_html=True
        )

    # 截斷 summary（摘要，使用較小的限制）
    if "summary" in result and result["summary"]:
        summary_limit = min(word_limit // 2, 200)  # 摘要最多為主體的一半，且不超過200字
        result["summary"] = truncate_text(
            result["summary"], summary_limit, preserve_html=False
        )

    # title 通常不需要截斷，但設一個合理的上限
    if "title" in result and result["title"]:
        result["title"] = truncate_text(result["title"], 50, preserve_html=False)

    return result
