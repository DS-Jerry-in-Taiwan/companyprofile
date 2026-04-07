# prompt_builder.py
"""
Prompt Builder
- 組裝 LLM Prompt
"""


def build_generate_prompt(
    organ, organ_no=None, company_url=None, user_brief=None, web_content=None
):
    """
    組裝 GENERATE 模式的完整 prompt，包含所有素材。

    Args:
        organ: 公司名稱（必需）
        organ_no: 統一編號（可選）
        company_url: 公司官網（可選）
        user_brief: 用戶提供的簡介素材（可選）
        web_content: 網路搜尋取得的內容（可選）

    Returns:
        組裝好的 prompt 字串
    """
    sections = []

    # 1. 基礎資訊
    sections.append(f"## 公司基本資訊")
    sections.append(f"公司名稱：{organ}")
    if organ_no:
        sections.append(f"統一編號：{organ_no}")
    if company_url:
        sections.append(f"官網：{company_url}")

    # 2. 用戶提供的素材
    if user_brief:
        sections.append(f"\n## 用戶提供的素材")
        sections.append(f"{user_brief}")

    # 3. 網路搜尋取得的內容
    if web_content:
        sections.append(f"\n## 網路搜尋取得的資訊")
        sections.append(f"{web_content}")

    # 4. 輸出要求
    sections.append(f"\n## 輸出要求")
    sections.append("請根據上述所有資訊，生成一段專業、簡潔的公司簡介（200-300字）。")
    sections.append("如有用戶提供的素材，請優先參考並整合。")

    return "\n".join(sections)
