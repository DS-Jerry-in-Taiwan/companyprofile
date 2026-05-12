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

# ============================================================
# Phase 32: 第一人稱範例庫（模組化，隨機組合）
# ============================================================

# 1. 直接開頭型 — 以「我們」開頭，最基礎的寫法
WE_DIRECT_EXAMPLES = {
    "concise": [
        """【正確輸出】
我們自成立以來，專注於資訊安全領域，客戶涵蓋金融與醫療產業。""",
        """【正確輸出】
我們致力於環保技術開發，以廢棄物資源化為核心業務。""",
    ],
    "standard": [
        """【正確輸出】
我們自2010年成立以來，專注於資訊安全與雲端運算領域，客戶涵蓋金融、醫療與製造等產業，以自主研發的AI偵測系統獲得業界肯定。""",
    ],
    "detailed": [
        """【正確輸出】
我們自2010年成立以來，總部位於台北市內湖科技園區，專注於資訊安全與雲端運算領域。我們自主研發的AI威脅偵測系統可即時攔截網路攻擊，準確率高達99.5%，服務客戶涵蓋金融、醫療、製造與政府機關等四大產業，以「安全即服務」為核心理念持續投入研發。""",
    ],
}


# 2. 主詞省略型 — 開頭不帶主詞（解決「我們」過多的核心方案）
WE_OMIT_EXAMPLES = {
    "concise": [
        """【正確輸出】
自成立以來，專注於資訊安全領域，客戶涵蓋金融與醫療產業。""",
        """【正確輸出】
致力於環保技術開發，以廢棄物資源化為核心業務。""",
    ],
    "standard": [
        """【正確輸出】
自2010年成立以來，專注於資訊安全與雲端運算領域，客戶涵蓋金融、醫療與製造等產業。自主研發的AI偵測系統獲得業界肯定。""",
        """【正確輸出】
於2015年創立，深耕環保技術領域，以廢棄物資源化為核心業務，累積超過百件成功案例。""",
    ],
    "detailed": [
        """【正確輸出】
自2010年成立以來，深耕資訊安全與雲端運算領域。自主研發的AI威脅偵測系統可即時攔截網路攻擊，準確率高達99.5%，服務客戶涵蓋金融、醫療、製造與政府機關等四大產業。""",
    ],
}


# 3. 角色融入型 — 以「身為...」「作為...」開頭
WE_ROLE_EXAMPLES = {
    "standard": [
        """【正確輸出】
身為綠色能源領域的專業廠商，我們致力於環保技術開發，以廢棄物資源化為核心業務，服務涵蓋工業廢水處理與再生能源設備。""",
    ],
    "detailed": [
        """【正確輸出】
身為台灣綠色能源領域的專業廠商，我們以廢棄物資源化為核心業務，服務涵蓋工業廢水處理、再生能源設備與環境影響評估。團隊擁有超過50位專業人才，累積完成超過300件專案。""",
    ],
}


# 4. 使命願景型 — 以「我們的使命/願景」開頭
WE_MISSION_EXAMPLES = {
    "concise": [
        """【正確輸出】
我們的使命是透過創意設計幫助品牌發光。團隊約25人，專注於品牌設計與數位行銷。""",
    ],
    "standard": [
        """【正確輸出】
我們的願景是成為台灣最具影響力的品牌設計團隊。自2018年成立以來，專注於品牌設計與數位行銷，以數據驅動的創意策略協助客戶打造差異化品牌體驗。""",
    ],
    "detailed": [
        """【正確輸出】
我們的使命是透過創意設計與數據驅動的策略，協助品牌在數位時代脫穎而出。自2018年成立以來，團隊約25人，營運據點位於台北市大安區，專注於品牌設計與數位行銷整合服務。""",
    ],
}


# 5. 提問開頭型 — 以「您是否...？」提問開頭
WE_QUESTION_EXAMPLES = {
    "standard": [
        """【正確輸出】
您是否正在尋找可靠的技術夥伴？我們自2010年成立以來，專注於資訊安全領域，以自主研發的AI系統獲得業界肯定。""",
    ],
    "detailed": [
        """【正確輸出】
您是否正在尋找值得信賴的綠色能源合作夥伴？我們自2015年成立以來，深耕環保技術領域，累積超過300件成功案例，客戶遍及半導體與電子製造業。""",
    ],
}


# 6. 情境鋪陳型 — 先鋪陳產業背景，再帶入公司
WE_SCENE_EXAMPLES = {
    "standard": [
        """【正確輸出】
在資訊安全威脅日益嚴峻的時代，我們致力於提供全方位的資安解決方案，協助企業抵禦網路攻擊，守護數據安全。""",
    ],
    "detailed": [
        """【正確輸出】
在全球環保意識抬頭與淨零排放趨勢下，我們致力於綠色能源技術的研發與應用。自2015年成立以來，以廢棄物資源化為核心業務，累積完成超過300件專案，為台灣循環經濟發展貢獻心力。""",
    ],
}


# 7. 混用錯誤型（固定保留）

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
    if company_url:
        sections.append(f"官網：{company_url}")

    # Phase 21: user_input 是 dict，直接格式化輸出
    # Phase 31: 過濾不該顯示給 LLM 的欄位（資本額、員工人數）
    display_input = {k: v for k, v in user_input.items() if k not in ('capital', 'employees')} if user_input else None
    if display_input:
        sections.append(f"\n## 用戶提供的素材")
        sections.append(format_content(display_input))

    # 2. 網路搜尋取得的內容
    if web_content:
        sections.append(f"\n## 網路搜尋取得的資訊")
        sections.append(f"{web_content}")

    # 3. 必須使用的關鍵資訊清單（使用數字標記法）
    # Phase 31: 改為對求職者有用的資訊，不再強制要求資本額
    required_info = []
    required_numbers = []
    jobseeker_info = []
    if user_input:
        if user_input.get("capital"):
            required_numbers.append(user_input["capital"])
        if user_input.get("employees"):
            required_numbers.append(user_input["employees"])
        if user_input.get("founded_year"):
            required_numbers.append(user_input["founded_year"])
            jobseeker_info.append(f"[成立年份]: {user_input['founded_year']}")
        if user_input.get("industry") or user_input.get("industry_desc"):
            jobseeker_info.append("[產業領域]: 核心業務與市場定位")
        if user_input.get("brand_names"):
            jobseeker_info.append(f"[品牌名稱]: {user_input['brand_names']}")

        # Phase 38: config 定義的欄位自動 inject（只進 config 有的，防止 LLM 飄移）
        from src.services.field_processor import FieldProcessor
        processor = FieldProcessor()
        for item in processor.get_prompt_items(user_input):
            if item not in jobseeker_info:
                jobseeker_info.append(item)

    # Phase 32: 模組化範例選取（隨機組合不同風格）
    import random
    
    # ═══ 範例區塊（永遠執行，不依賴 user_input） ═══
    _few_mode = optimization_mode.lower() if optimization_mode else "standard"
    if _few_mode not in ("concise", "standard", "detailed"):
        _few_mode = "standard"
    
    style_name_map = {
        "WE_DIRECT": "direct",
        "WE_OMIT": "omit",
        "WE_ROLE": "role",
        "WE_MISSION": "mission",
        "WE_QUESTION": "question",
        "WE_SCENE": "scene",
    }
    pools = {
        "concise": [
            (WE_DIRECT_EXAMPLES["concise"], 1, "direct"),
            (WE_OMIT_EXAMPLES["concise"], 1, "omit"),
            (WE_MISSION_EXAMPLES["concise"], 1, "mission"),
        ],
        "standard": [
            (WE_DIRECT_EXAMPLES["standard"], 1, "direct"),
            (WE_OMIT_EXAMPLES["standard"], 1, "omit"),
            (WE_ROLE_EXAMPLES["standard"], 1, "role"),
            (WE_QUESTION_EXAMPLES["standard"], 1, "question"),
            (WE_SCENE_EXAMPLES["standard"], 1, "scene"),
        ],
        "detailed": [
            (WE_DIRECT_EXAMPLES["detailed"], 1, "direct"),
            (WE_OMIT_EXAMPLES["detailed"], 1, "omit"),
            (WE_ROLE_EXAMPLES["detailed"], 1, "role"),
            (WE_MISSION_EXAMPLES["detailed"], 1, "mission"),
            (WE_SCENE_EXAMPLES["detailed"], 1, "scene"),
        ],
    }
    
    selected_examples = []
    selected_styles = []
    
    # 隨機選取 1~2 種風格（取代之前全選）
    pool_list = pools[_few_mode]
    num_to_select = random.randint(1, min(2, len(pool_list)))
    selected_pools = random.sample(pool_list, num_to_select)
    
    for pool, count, style_name in selected_pools:
        selected = random.sample(pool, min(count, len(pool)))
        selected_examples.extend(selected)
        selected_styles.append(style_name)
    
    # 記錄選取的風格到 metadata
    if _metadata is not None:
        _metadata["fewshot_styles"] = ",".join(selected_styles)
    
    # 組裝成 sections
    sections.append(f"\n## 範例參考（{_few_mode} 模式 — 隨機組合）")
    for i, example in enumerate(selected_examples, 1):
        sections.append(f"\n### 範例 {i}")
        sections.append(example)
    
    # ═══ 範例區塊結束 ═══

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

    # 硬性要求（含對求職者有用的資訊 + 應避免的資訊）
    if jobseeker_info or required_numbers:
        sections.append(f"\n### ⚠️ 硬性要求（必須遵守）")
        
        # 對求職者有用的資訊
        if jobseeker_info:
            sections.append("1. 優先呈現對求職者有用的資訊：")
            for info in jobseeker_info:
                sections.append(f"   - {info}")
        
        # 應避免的資訊
        sections.append("")
        sections.append("2. 應避免的資訊（對求職者無意義）：")
        sections.append("   - 統一編號（廠商編號）")
        sections.append("   - 實收資本額、登記資本額")
        sections.append("   - 經濟部商業司核准設立等行政登記資訊")
        sections.append("   - 負責人姓名、公司登記地址（若與上班地點無關）")
        
        sections.append("")
        sections.append("3. 請以自然的方式將上述有用資訊融入內容中")
        sections.append("4. ⚠️ 重要：必須優先使用上方『公司基本資訊』中提供的數據")
        sections.append("5. 如果搜尋結果與上方提供的基本資訊有衝突，請以基本資訊為準")
        sections.append("6. 搜尋結果僅供參考，核心數據必須使用上方提供的資訊")
        sections.append(
            "7. 請直接輸出最終內容，不必在輸出中進行任何檢查說明或驗證過程"
        )

    # Phase 30: 寫作視角要求 — 角色扮演：公司人資/公關
    sections.append("\n### 寫作視角")
    sections.append("- 請以該公司人資或公關的角色，用第一人稱向求職者介紹公司")
    sections.append("- 用「我們」來描述公司，但不要生硬地重複「我們公司名稱」")
    sections.append("- 可以靈活切換多種第一人稱表達，例如：")
    sections.append("  • 直接以「我們」開頭：「我們自成立以來...」")
    sections.append("  • 以公司角色融入：「身為國內的領導品牌，我們...」")
    sections.append("  • 以使命願景開頭：「我們的使命是...」")
    sections.append("  • 以面向求職者的提問開頭：「您是否正在尋找...？我們...」")
    sections.append("- 請勿使用第三人稱外部介紹語氣，如「該公司成立於...」、「該企業...」、「這家公司...」")
    sections.append("- ⚠️ 整篇簡介從頭到尾都要維持第一人稱，不可中途切換為第三人稱")

    sections.append("\n### 品質要求")
    sections.append("- 如有用戶提供的素材，請優先參考並整合")
    sections.append("- 確保內容準確、專業、易讀")
    sections.append("- 使用台灣常用語彙，避免中國大陸常用詞語")
    sections.append("- 例如：請用「網路」而非「網絡」、用「印表機」而非「打印機」、用「伺服器」而非「服務器」")

    # Phase 25: 數字格式規範 - 避免千位逗號
    sections.append("\n### 數字格式規範")
    sections.append("- 所有數字請勿使用千位逗號分隔")
    sections.append("- 例如：請寫「2582526570」而非「2,582,526,570」")
    sections.append("- 貨幣金額格式為：新台幣 2582526570 元（無逗號）")

    # Phase 14 Stage 3: 字數限制（改為約束條件，移除審查要求）
    sections.append("\n### 字數限制")
    sections.append(f"輸出長度範圍：{template_info['length_guide']}")
    sections.append(
        "請嚴格遵守字數限制。直接輸出最終內容，不要輸出字數統計、檢查過程或任何非簡介內容。"
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
