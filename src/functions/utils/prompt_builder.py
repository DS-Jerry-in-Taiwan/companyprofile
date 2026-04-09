# prompt_builder.py
"""
Prompt Builder
- 組裝 LLM Prompt
- 包含 Few-shot 範例以提升資訊使用率
"""

# Few-shot 範例：展示如何正確使用數字資訊
FEW_SHOT_EXAMPLES = """
## 範例參考（請學習以下範例的寫法）

### 範例一：包含資本額與員工人數
【輸入資訊】
- 公司名稱：ABC科技有限公司
- 資本額：5000萬元
- 員工人數：200人

【正確輸出】
ABC科技有限公司專注於創新技術研發，資本額達5000萬元，員工人數約200人，致力於為客戶提供高品質的科技解決方案。

【錯誤輸出】❌
ABC科技有限公司是一家專注於創新技術研發的企業，致力於為客戶提供優質服務。
（錯誤原因：未使用資本額和員工人數）

---

### 範例二：包含成立年份
【輸入資訊】
- 公司名稱：綠能環保股份有限公司
- 成立年份：2015年
- 資本額：2億元

【正確輸出】
綠能環保股份有限公司成立於2015年，資本額2億元，專注於環保技術與綠色能源開發，為永續發展貢獻心力。

【錯誤輸出】❌
綠能環保股份有限公司是一家專注於環保技術與綠色能源開發的企業，為永續發展貢獻心力。
（錯誤原因：未使用成立年份和資本額）

---

### 範例三：完整資訊
【輸入資訊】
- 公司名稱：數位創意工作室
- 成立年份：2018年
- 資本額：800萬元
- 員工人數：25人

【正確輸出】
數位創意工作室成立於2018年，資本額800萬元，擁有約25名專業團隊成員，專注於數位設計與創意服務，為客戶打造獨特的數位體驗。
"""


def build_generate_prompt(
    organ,
    organ_no=None,
    company_url=None,
    user_brief=None,
    web_content=None,
    word_limit=None,
    capital=None,
    employees=None,
    founded_year=None,
):
    """
    組裝 GENERATE 模式的完整 prompt，包含所有素材。

    Args:
        organ: 公司名稱（必需）
        organ_no: 統一編號（可選）
        company_url: 公司官網（可選）
        user_brief: 用戶提供的簡介素材（可選）
        web_content: 網路搜尋取得的內容（可選）
        word_limit: 字數限制（可選，預設為 300）
        capital: 資本額（可選）
        employees: 員工人數（可選）
        founded_year: 成立年份（可選）

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
    if capital:
        # 將資本額轉換為「萬元」顯示，更易讀
        capital_wan = capital / 10000
        if capital_wan >= 10000:
            sections.append(f"資本額：{capital_wan / 10000:.2f} 億元")
        else:
            sections.append(f"資本額：{capital_wan:.0f} 萬元")
    if employees:
        sections.append(f"員工人數：約 {employees} 人")
    if founded_year:
        sections.append(f"成立年份：西元 {founded_year} 年")

    # 2. 用戶提供的素材
    if user_brief:
        sections.append(f"\n## 用戶提供的素材")
        sections.append(f"{user_brief}")

    # 3. 網路搜尋取得的內容
    if web_content:
        sections.append(f"\n## 網路搜尋取得的資訊")
        sections.append(f"{web_content}")

    # 4. 必須使用的關鍵資訊清單（使用數字標記法）
    required_info = []
    required_numbers = []  # 用於驗證的數字列表
    if capital:
        # 統一使用「萬元」或「億元」單位
        capital_wan = capital / 10000
        if capital_wan >= 10000:
            required_info.append(f"[資本額]: {capital_wan / 10000:.2f} 億元")
            required_numbers.append(f"{capital_wan / 10000:.2f} 億")
        else:
            required_info.append(f"[資本額]: {capital_wan:.0f} 萬元")
            required_numbers.append(f"{capital_wan:.0f} 萬")
    if employees:
        required_info.append(f"[員工人數]: 約 {employees} 人")
        required_numbers.append(f"{employees}")
    if founded_year:
        required_info.append(f"[成立年份]: {founded_year} 年")
        required_numbers.append(f"{founded_year}")

    # 5. 加入 Few-shot 範例（當有選填資訊時）
    if required_info:
        sections.append(f"\n{FEW_SHOT_EXAMPLES}")

    # 6. 輸出要求
    sections.append(f"\n## 輸出要求")

    # 動態設置字數限制
    if word_limit:
        sections.append(
            f"請根據上述所有資訊，生成一段專業、簡潔的公司簡介（不超過 {word_limit} 字）。"
        )
    else:
        sections.append(
            "請根據上述所有資訊，生成一段專業、簡潔的公司簡介（200-300字）。"
        )

    # 強制要求使用所有資訊
    if required_info:
        sections.append(f"\n### ⚠️ 硬性要求（必須遵守）")
        sections.append("1. 生成的簡介必須包含以下所有關鍵資訊：")
        for info in required_info:
            sections.append(f"   - {info}")
        sections.append("2. 不得遺漏任何上述數值資訊")
        sections.append("3. 請用自然的方式將這些資訊融入內容中")
        sections.append("4. ⚠️ 重要：必須優先使用上方『公司基本資訊』中提供的數據")
        sections.append("5. 如果搜尋結果與上方提供的基本資訊有衝突，請以基本資訊為準")
        sections.append("6. 搜尋結果僅供參考，核心數據必須使用上方提供的資訊")
        sections.append(
            "7. ✅ 檢查點：生成後請自我檢查，確保所有標記的數字都已出現在輸出中"
        )

        # 提供檢查清單
        sections.append(f"\n### ✅ 生成後檢查清單")
        sections.append(f"請確認輸出包含以下數字：{', '.join(required_numbers)}")

    sections.append("\n### 品質要求")
    sections.append("- 如有用戶提供的素材，請優先參考並整合")
    sections.append("- 確保內容準確、專業、易讀")
    sections.append("- 使用台灣常用語彙")

    return "\n".join(sections)


def validate_info_usage(output_text, capital=None, employees=None, founded_year=None):
    """
    驗證生成內容是否使用了所有必要的資訊。

    Args:
        output_text: LLM 生成的簡介文字
        capital: 資本額（可選）
        employees: 員工人數（可選）
        founded_year: 成立年份（可選）

    Returns:
        tuple: (is_valid: bool, missing_info: list)
            - is_valid: 是否通過驗證
            - missing_info: 缺失的資訊列表
    """
    import re

    missing = []

    # 檢查資本額
    if capital:
        capital_wan = capital / 10000
        capital_ok = False

        # 嘗試多種可能的形式
        if capital_wan >= 10000:
            # 億元格式
            capital_ok = (
                f"{capital_wan / 10000:.2f}" in output_text
                or f"{capital_wan / 10000:.1f}" in output_text
                or f"{int(capital_wan / 10000)}" in output_text
                or f"{capital_wan / 10000:.2f}億" in output_text
            )
        else:
            # 萬元格式
            capital_ok = (
                f"{capital_wan:.0f}萬" in output_text
                or f"{capital_wan:.0f} 萬" in output_text
                or str(int(capital_wan)) in output_text
            )

        if not capital_ok:
            missing.append(
                f"資本額 (應包含: {capital_wan / 10000:.2f}億元)"
                if capital_wan >= 10000
                else f"資本額 (應包含: {capital_wan:.0f}萬元)"
            )

    # 檢查員工人數
    if employees:
        employees_ok = (
            f"{employees}" in output_text
            or f"{employees}人" in output_text
            or f"{employees} 人" in output_text
        )
        if not employees_ok:
            missing.append(f"員工人數 (應包含: {employees}人)")

    # 檢查成立年份
    if founded_year:
        year_ok = (
            f"{founded_year}" in output_text
            or f"{founded_year}年" in output_text
            or f"{founded_year} 年" in output_text
        )
        if not year_ok:
            missing.append(f"成立年份 (應包含: {founded_year}年)")

    return len(missing) == 0, missing
