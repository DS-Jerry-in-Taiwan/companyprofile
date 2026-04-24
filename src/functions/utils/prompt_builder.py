# prompt_builder.py
"""
Prompt Builder
- 組裝 LLM Prompt
- 包含 Few-shot 範例以提升資訊使用率
- Phase 14 Stage 2: 支援三模板差異化提示詞
- Phase 23: 注入框架/情境/句型多樣化指導（v0.3.8）
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Phase 23: 惰性導入 structure_library（避免循環依賴）
_STRUCTURE_LIBRARY = None


def _get_structure_library():
    """惰性載入 structure_library 模組"""
    global _STRUCTURE_LIBRARY
    if _STRUCTURE_LIBRARY is None:
        try:
            from src.functions.utils.structure_library import (
                get_random_structure,
                get_random_opening,
                get_random_sentence_pattern,
                get_structure_flow,
                STRUCTURE_NAMES,
                SITUATION_OPENINGS,
                SENTENCE_PATTERNS,
                SITUATION_NAMES,
                SENTENCE_NAMES,
            )

            _STRUCTURE_LIBRARY = {
                "get_random_structure": get_random_structure,
                "get_random_opening": get_random_opening,
                "get_random_sentence_pattern": get_random_sentence_pattern,
                "get_structure_flow": get_structure_flow,
                "STRUCTURE_NAMES": STRUCTURE_NAMES,
                "SITUATION_OPENINGS": SITUATION_OPENINGS,
                "SENTENCE_PATTERNS": SENTENCE_PATTERNS,
                "SITUATION_NAMES": SITUATION_NAMES,
                "SENTENCE_NAMES": SENTENCE_NAMES,
            }
        except ImportError:
            logger.warning("structure_library 模組不可用，多樣化功能將跳過")
            _STRUCTURE_LIBRARY = {}
    return _STRUCTURE_LIBRARY


# Phase 23: 框架段落區塊標題對應（用於生成段落順序提示）
STRUCTURE_SECTION_TITLES = {
    "foundation": "成立背景與基本資訊",
    "core": "核心服務與產品",
    "vibe": "企業理念與競爭力",
    "future": "未來展望與發展方向",
    "core_values": "核心價值與理念",
    "core_features": "核心特色與優勢",
    "scale": "企業規模與資本",
}

# Phase 23: 框架段落順序說明（中文）
STRUCTURE_FLOW_DESCRIPTIONS = {
    "traditional": "先介紹公司背景，再說明服務與競爭力，最後展望未來",
    "service_first": "從核心服務切入，再補充公司背景與特色",
    "value_first": "以核心價值與理念開場，帶出公司背景與服務",
    "future_oriented": "先描繪願景與未來方向，再回顧公司背景與核心能力",
    "feature_first": "從核心特色與優勢開始，再說明公司背景與服務",
    "data_oriented": "以企業規模和資本數據開頭，再介紹背景與核心業務",
}

# Phase 23: 開頭風格說明（用於多樣化指導）
OPENING_DESCRIPTIONS = {
    "industry": "以產業情境開頭：先鋪陳公司所處的產業背景，再自然帶出公司",
    "market": "以市場情境開頭：先描述市場變化或趨勢，再帶出公司在市場中的定位",
    "problem": "以問題情境開頭：先點出行業面臨的挑戰或痛點，再帶出公司的解決方案",
    "trend": "以趨勢情境開頭：先說明產業發展趨勢，再帶出公司順應趨勢的布局",
    "user": "以使用者情境開頭：從目標客戶的需求或場景切入，再帶出公司的服務",
}

# Phase 23: 句型風格說明（用於多樣化指導）
SENTENCE_DESCRIPTIONS = {
    "service": "服務導向：以「專注於[產業]的[公司]，提供[服務]」的結構強調服務內容",
    "feature": "特色導向：以「以[特色]聞名的[公司]，[行動]」的結構突顯獨特優勢",
    "data": "數據導向：以「擁有[歷史]年歷史的[公司]，[描述]」的結構強調經驗與規模",
    "question": "問句式：以提問引起讀者共鳴與好奇，再帶出公司的解決方案",
    "situation": "情境描述：先描繪具體場景或情境，再帶出公司在該情境中扮演的角色",
    "achievement": "成就導向：以「作為[產業]領域的領導者，[公司]...」彰顯市場地位",
    "commitment": "承諾導向：以「[公司]致力於[服務]...」展現公司使命與價值主張",
}

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

# Phase 14 Stage 3: 字數限制優化 - 模板類型描述
# 新架構：Prompt 層控制 + 字數檢核 + 必要時 LLM 重寫
TEMPLATE_DESCRIPTIONS = {
    "concise": {
        "name": "精簡模式",
        # 字數範圍（上下限）- 用於 Prompt 提示與檢核
        "length_min": 40,
        "length_max": 120,
        "length_guide": "40-120字（最佳範圍）",
        "content_guide": (
            "請生成一段極簡的公司簡介，只保留公司名稱和最核心業務。"
            "風格要簡潔直接，避免修飾性詞語、避免使用「此外」「另外」「同時」等連接詞。"
            "1-2句話即可，字數控制在40-120字之間。"
            "重要：生成後請自行檢查字數，確保在40-120字範圍內。"
        ),
    },
    "standard": {
        "name": "標準模式",
        # 字數範圍（上下限）
        "length_min": 130,
        "length_max": 230,
        "length_guide": "130-230字（最佳範圍）",
        "content_guide": (
            "請生成一段平衡的公司簡介，包含公司背景、核心服務和主要特色。"
            "內容要專業自然，3-5句話，讓讀者對公司有清晰印象，字數控制在130-230字之間。"
            "重要：生成後請自行檢查字數，確保在130-230字範圍內。"
        ),
    },
    "detailed": {
        "name": "詳細模式",
        # 字數範圍（上下限）
        "length_min": 280,
        "length_max": 550,
        "length_guide": "280-550字（最佳範圍）",
        "content_guide": (
            "請生成一段詳細全面的公司簡介，涵蓋以下面向：成立背景與歷程、主要服務與產品、"
            "核心競爭力、團隊規模與文化、市場定位與客戶群、未來發展願景。"
            "內容要豐富完整，分段清楚，字數控制在280-550字之間。"
            "重要：生成後請自行檢查字數，確保在280-550字範圍內。"
        ),
    },
}


# ============================================================
# Phase 23: 多樣化指導區塊建構
# ============================================================


def _build_structure_guide(structure_key: str) -> str:
    """建構框架指導文字"""
    lib = _get_structure_library()
    if not lib:
        return ""
    get_flow = lib["get_structure_flow"]
    names = lib["STRUCTURE_NAMES"]
    flow = get_flow(structure_key)
    name = names.get(structure_key, structure_key)
    flow_desc = STRUCTURE_FLOW_DESCRIPTIONS.get(structure_key, "")

    # 將段落 key 轉換為中文標題
    section_titles = [STRUCTURE_SECTION_TITLES.get(k, k) for k in flow]
    sections_str = " → ".join(section_titles)

    parts = [
        f"框架類型：{name}（{structure_key}）",
        f"段落順序建議：{flow_desc}",
        f"具體安排：{sections_str}",
    ]
    return "\n".join(parts)


def _build_opening_guide(opening_key: str) -> str:
    """建構開頭風格指導文字"""
    desc = OPENING_DESCRIPTIONS.get(opening_key, "")
    names = {
        "industry": "產業情境",
        "market": "市場情境",
        "problem": "問題情境",
        "trend": "趨勢情境",
        "user": "使用者情境",
    }
    name = names.get(opening_key, opening_key)
    return f"開頭風格：{name}\n說明：{desc}"


def _build_sentence_guide(sentence_key: str) -> str:
    """建構句型風格指導文字"""
    desc = SENTENCE_DESCRIPTIONS.get(sentence_key, "")
    names = {
        "service": "服務導向",
        "feature": "特色導向",
        "data": "數據導向",
        "question": "問句式",
        "situation": "情境描述",
        "achievement": "成就導向",
        "commitment": "承諾導向",
    }
    name = names.get(sentence_key, sentence_key)
    return f"句型風格：{name}\n說明：{desc}"


def build_diversity_guide(
    structure_key: str = "traditional",
    opening_key: str = "industry",
    sentence_key: str = "service",
) -> str:
    """
    建構多樣化指導區塊內容

    生成一段「結構與風格多樣化指導」文字，
    包含框架類型、開頭風格、句型風格三方面的說明。

    Args:
        structure_key: 框架 key
        opening_key: 情境 key
        sentence_key: 句型 key

    Returns:
        格式化的多樣化指導字串
    """
    guide_parts = ["\n## 結構與風格多樣化指導", ""]

    # 框架
    structure_guide = _build_structure_guide(structure_key)
    if structure_guide:
        guide_parts.append("### 框架指導")
        guide_parts.append(structure_guide)
        guide_parts.append("")

    # 開頭
    opening_guide = _build_opening_guide(opening_key)
    if opening_guide:
        guide_parts.append("### 開頭指導")
        guide_parts.append(opening_guide)
        guide_parts.append("")

    # 句型
    sentence_guide = _build_sentence_guide(sentence_key)
    if sentence_guide:
        guide_parts.append("### 句型指導")
        guide_parts.append(sentence_guide)
        guide_parts.append("")

    guide_parts.append("### 執行要求")
    guide_parts.append("1. 請依照上述框架指導安排段落順序")
    guide_parts.append("2. 參考開頭風格撰寫開場白，可依據選擇的情境選擇適合的開頭方式")
    guide_parts.append("3. 運用指定的句型變化，避免通篇使用相同句型結構")

    return "\n".join(guide_parts)


# ============================================================


def build_generate_prompt(
    organ,
    organ_no=None,
    company_url=None,
    user_input=None,
    web_content=None,
    word_limit=None,
    optimization_mode=None,
    # Phase 23: 多樣化參數
    structure_key=None,
    opening_key=None,
    sentence_key=None,
    # Phase 24: 接收 dict，呼叫後會填入 framework metadata
    _metadata=None,
):
    """
    組裝 GENERATE 模式的完整 prompt，包含所有素材。

    Args:
        organ: 公司名稱（必需）
        organ_no: 統一編號（可選）
        company_url: 公司官網（可選）
        user_input: 用戶提供的簡介素材 dict（Phase 21 新增）
        web_content: 網路搜尋取得的內容（可選）
        word_limit: 字數限制（可選，預設為 300）
        optimization_mode: 模板類型 (concise/standard/detailed)（可選，預設為 standard）
        structure_key: 文章框架 key（Phase 23，可選，預設 random）
        opening_key: 開頭情境 key（Phase 23，可選，預設 random）
        sentence_key: 句型 key（Phase 23，可選，預設 random）
        _metadata: 傳入 dict 會被填入 framework metadata（Phase 24，不傳則無作用）

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

    # Phase 21: user_input 是 dict，直接格式化輸出
    if user_input:
        sections.append(f"\n## 用戶提供的素材")
        sections.append(format_content(user_input))

    # 2. 網路搜尋取得的內容
    if web_content:
        sections.append(f"\n## 網路搜尋取得的資訊")
        sections.append(f"{web_content}")

    # 3. 必須使用的關鍵資訊清單（使用數字標記法）
    # Phase 21: 從 user_input 取出數值欄位用於驗證
    required_info = []
    required_numbers = []
    if user_input:
        if user_input.get("capital"):
            required_info.append(f"[資本額]: {user_input['capital']}")
            required_numbers.append(user_input["capital"])
        if user_input.get("employees"):
            required_info.append(f"[員工人數]: {user_input['employees']}")
            required_numbers.append(user_input["employees"])
        if user_input.get("founded_year"):
            required_info.append(f"[成立年份]: {user_input['founded_year']}")
            required_numbers.append(user_input["founded_year"])

    # 5. 加入 Few-shot 範例（當有選填資訊時）
    if required_info:
        sections.append(f"\n{FEW_SHOT_EXAMPLES}")

    # 6. 輸出要求
    sections.append(f"\n## 輸出要求")

    # Phase 14 Stage 2: 根據模板類型提供差異化的輸出要求
    # 統一轉小寫以支援 API 層的 "CONCISE"/"STANDARD"/"DETAILED" 格式
    mode_key = optimization_mode.lower() if optimization_mode else None
    if mode_key and mode_key in TEMPLATE_DESCRIPTIONS:
        template_info = TEMPLATE_DESCRIPTIONS[mode_key]
        sections.append(f"\n### 📋 輸出模式：{template_info['name']}")
        sections.append(f"長度要求：{template_info['length_guide']}")
        sections.append(f"內容要求：{template_info['content_guide']}")
    else:
        # 預設為標準模式
        template_info = TEMPLATE_DESCRIPTIONS["standard"]
        sections.append(f"\n### 📋 輸出模式：{template_info['name']}")
        sections.append(f"長度要求：{template_info['length_guide']}")
        sections.append(f"內容要求：{template_info['content_guide']}")

    # 動態設置字數限制（作為輔助參考）
    if word_limit:
        sections.append(f"\n⚠️ 字數上限：不超過 {word_limit} 字。")
    elif not optimization_mode:
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

    # Phase 14 Stage 3: 字數限制優化 - 加入生成後自我檢查指令
    sections.append("\n### ✅ 生成後自我檢查（必須執行）")
    sections.append("1. 確認字數在指定範圍內")
    sections.append(
        f"2. 若超出範圍，請調整內容直到符合：{template_info['length_guide']}"
    )
    sections.append("3. 確保不要出現「...」或其他截斷符號")
    sections.append(
        "4. ⚠️ 重要：上述檢查只供內部參考，絕對不要在輸出內容中加入任何字數統計（如「(字數：XXX)」）"
    )

    # Phase 23: 加入多樣化指導區塊
    lib = _get_structure_library()
    if lib:
        # 如果未指定，就隨機選取
        if structure_key is None:
            structure_key = lib["get_random_structure"]()
        if opening_key is None:
            opening_key = lib["get_random_opening"]()
        if sentence_key is None:
            sentence_key = lib["get_random_sentence_pattern"]()

        diversity_guide = build_diversity_guide(
            structure_key=structure_key,
            opening_key=opening_key,
            sentence_key=sentence_key,
        )
        sections.append(diversity_guide)
        logger.info(
            f"[Phase23] Prompt 注入多樣化指導: "
            f"框架={structure_key}, 開頭={opening_key}, 句型={sentence_key}"
        )
    else:
        logger.warning("[Phase23] structure_library 不可用，跳過多樣化指導")

    # Phase 24: 填入 framework metadata（如果 caller 有傳 dict 進來）
    if _metadata is not None:
        # 解析有效的模板名稱
        mode_key = optimization_mode.lower() if optimization_mode else None
        if mode_key and mode_key in TEMPLATE_DESCRIPTIONS:
            _metadata["template_name"] = mode_key
        else:
            _metadata["template_name"] = "standard"
        # framework key（隨機或指定）
        _metadata["structure_key"] = structure_key
        _metadata["opening_key"] = opening_key
        _metadata["sentence_key"] = sentence_key

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


def format_content(data):
    """
    自動判斷資料格式並格式化輸出

    Args:
        data: dict，aspect_summaries 或 user_input 格式

    Returns:
        str: 格式化後的字串
    """
    if not data:
        return ""

    # 判斷格式：aspect 格式有 foundation/core/vibe/future 鍵
    if any(key in data for key in ["foundation", "core", "vibe", "future"]):
        # aspect 格式
        parts = []
        for key in ["foundation", "core", "vibe", "future"]:
            value = data.get(key)
            if value:
                if hasattr(value, "content"):
                    content = value.content
                else:
                    content = str(value)
                if content and content.strip():
                    parts.append(f"【{key}】\n{content}")
        return "\n\n".join(parts)
    else:
        # user_input 格式
        parts = []
        for key, value in data.items():
            if value:
                parts.append(f"{key}：{value}")
        return "\n".join(parts)
