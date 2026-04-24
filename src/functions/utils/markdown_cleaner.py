"""
Markdown Cleaner - 清理 LLM 輸出中的 Markdown 語法

Phase 22: 移除 **、##、### 等 Markdown 格式
確保輸出為乾淨的純文字或 HTML 格式

用法:
    from src.functions.utils.markdown_cleaner import clean_markdown
    result = clean_markdown("**公司名稱**")
    # → "公司名稱"
"""

import re


def clean_markdown(text: str) -> str:
    """
    清理文字中的 Markdown 語法（標準模式）

    處理:
    - **bold** → bold
    - ## Header → Header
    - ### Header → Header
    - # Header → Header

    保留:
    - ***-****-**** (電話格式)
    - <b>, <p> 等 HTML 標籤

    Args:
        text: 原始文字，可能包含 Markdown 語法

    Returns:
        str: 清理後的文字
    """
    if text is None:
        return None

    if not isinstance(text, str):
        return text

    if not text:
        return text

    # 0. 保護電話號碼格式 ***-****-****
    # 先用佔位符替換，清理完再還原
    PHONE_PLACEHOLDER = "__PHONE_PROTECT__"
    phone_pattern = re.compile(r'(?:\d+-)?\*{3}-\*{3,4}-\*{3,4}')
    protected_phones = []
    def _protect_phone(m):
        protected_phones.append(m.group(0))
        return PHONE_PLACEHOLDER
    text = phone_pattern.sub(_protect_phone, text)

    # 1. 移除 **bold** 語法
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

    # 2. 移除空 ****
    text = re.sub(r'\*\*\*\*', '', text)

    # 3. 移除 ### 三級標題
    text = re.sub(r'^###\s+', '', text, flags=re.MULTILINE)

    # 4. 移除 ## 二級標題
    text = re.sub(r'^##\s+', '', text, flags=re.MULTILINE)

    # 5. 移除 # 一級標題
    text = re.sub(r'^#\s+', '', text, flags=re.MULTILINE)

    # 6. 還原被保護的電話號碼
    for phone in protected_phones:
        text = text.replace(PHONE_PLACEHOLDER, phone, 1)

    return text


def clean_markdown_aggressive(text: str) -> str:
    """
    激進清理模式 - 移除所有 Markdown 語法

    額外處理:
    - *italic* → italic
    - `code` → code
    - - list → list

    Args:
        text: 原始文字

    Returns:
        str: 清理後的文字
    """
    if text is None:
        return None

    if not isinstance(text, str):
        return text

    if not text:
        return text

    # 標準清理
    text = clean_markdown(text)

    # 額外: 移除 *italic*
    text = re.sub(r'\*([^*]+)\*', r'\1', text)

    # 額外: 移除 `code`
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # 額外: 移除 - 列表符號
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)

    # 額外: 移除 > 引用
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    return text


# ========== 測試入口 ==========
if __name__ == "__main__":
    test_cases = [
        ("**bold**", "bold"),
        ("**艾兒莫拉韓系服飾**秉持著專業", "艾兒莫拉韓系服飾秉持著專業"),
        ("## 公司簡介\n內容", "公司簡介\n內容"),
        ("### 服務項目\n內容", "服務項目\n內容"),
        ("# 一級標題\n內容", "一級標題\n內容"),
        ("這是正常文字", "這是正常文字"),
        ("聯絡電話：***-****-****", "聯絡電話：***-****-****"),
        ("手機：0912-345-678", "手機：0912-345-678"),
        ("", ""),
        (None, None),
    ]

    all_passed = True
    for input_text, expected in test_cases:
        result = clean_markdown(input_text)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"{status} clean_markdown({input_text!r})")
        print(f"   expected: {expected!r}")
        print(f"   got:      {result!r}")
        print()

    if all_passed:
        print("🎉 所有測試通過！")
    else:
        print("⚠️ 部分測試失敗")
