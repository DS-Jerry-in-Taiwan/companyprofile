"""
Phase 23: 模板多樣化庫

提供三種模板庫來解決「模板過於一致」與「句型僵化」問題：
1. 文章框架庫 — 段落順序多樣化（6 種）
2. 情境庫 — 開頭情境描述（5 種）
3. 句型庫 — 句型多樣化（5+ 種）

使用方式：
    from src.functions.utils.structure_library import (
        get_random_structure,
        get_random_opening,
        get_random_sentence_pattern,
    )
"""

import random
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# ============================================================
# Step 4: 文章框架庫 — 定義 6 種段落順序
# ============================================================
# 每個框架定義為段落 key 的列表，依照輸出順序排列
# 段落 key 說明：
#   foundation: 成立背景（傳統結構中的「成立」）
#   core: 核心服務/產品（傳統結構中的「服務」）
#   vibe: 理念/競爭力（傳統結構中的「理念」+「競爭力」）
#   future: 未來展望（傳統結構中的「未來」）
#   core_values: 核心價值（取代 vibe，用於價值優先）
#   core_features: 核心特色（取代 core，用於特色優先）
#   scale: 規模/資本（取代 foundation，用於數據導向）

ARTICLE_STRUCTURES: Dict[str, List[str]] = {
    "traditional": ["foundation", "core", "vibe", "future"],
    "service_first": ["core", "foundation", "vibe", "future"],
    "value_first": ["core_values", "foundation", "core", "future"],
    "future_oriented": ["future", "foundation", "core", "vibe"],
    "feature_first": ["core_features", "foundation", "core", "future"],
    "data_oriented": ["scale", "foundation", "core", "future"],
}

# 框架中文名稱（用於日誌和除錯）
STRUCTURE_NAMES: Dict[str, str] = {
    "traditional": "傳統結構",
    "service_first": "服務優先",
    "value_first": "價值優先",
    "future_oriented": "未來導向",
    "feature_first": "特色優先",
    "data_oriented": "數據導向",
}

# 框架說明（適用場景）
STRUCTURE_DESCRIPTIONS: Dict[str, str] = {
    "traditional": "成立→理念→服務→競爭力→未來 — 適用於大眾、傳產",
    "service_first": "服務核心→成立→特色→未來 — 適用於服務業",
    "value_first": "核心價值→成立→服務→未來 — 適用於品牌導向",
    "future_oriented": "願景→成立→核心→服務 — 適用於新創、科技",
    "feature_first": "核心特色→成立→服務→未來 — 適用於差異化公司",
    "data_oriented": "資本/規模→成立→核心→未來 — 適用於上市公司",
}

# ============================================================
# Step 5: 情境庫 — 定義 5 種情境開頭
# ============================================================
# 使用 Python format 變數替換，變數需在呼叫時提供

SITUATION_OPENINGS: Dict[str, str] = {
    "industry": "在{industry}領域，{company}",
    "market": "面對{trend}，{company}",
    "problem": "針對{challenge}，{company}",
    "trend": "隨著{trend}，{company}",
    "user": "當你需要{service}，{company}",
}

# 情境中文名稱
SITUATION_NAMES: Dict[str, str] = {
    "industry": "產業情境",
    "market": "市場情境",
    "problem": "問題情境",
    "trend": "趨勢情境",
    "user": "使用者情境",
}

# 情境預設值（當未提供變數時的 fallback 用語）
SITUATION_DEFAULTS: Dict[str, Dict[str, str]] = {
    "industry": {"industry": "該產業"},
    "market": {"trend": "市場變化"},
    "problem": {"challenge": "行業挑戰"},
    "trend": {"trend": "產業趨勢"},
    "user": {"service": "專業服務"},
}

# ============================================================
# Step 6: 句型庫 — 定義 5+ 種句型
# ============================================================

SENTENCE_PATTERNS: Dict[str, str] = {
    "service": "專注於{industry}的{company}，提供{service}。",
    "feature": "以{feature}聞名的{company}，{action}。",
    "data": "擁有{years}年歷史的{company}，{description}。",
    "question": "想找{service}嗎？{company}是您的最佳選擇。",
    "situation": "{situation}，{company}{action}。",
    # 額外句型（超過 5 種）
    "achievement": "作為{industry}領域的領導者，{company}{action}。",
    "commitment": "{company}致力於{service}，{description}。",
}

# 句型中文名稱
SENTENCE_NAMES: Dict[str, str] = {
    "service": "服務導向",
    "feature": "特色導向",
    "data": "數據導向",
    "question": "問句式",
    "situation": "情境描述",
    "achievement": "成就導向",
    "commitment": "承諾導向",
}

# ============================================================
# 共用工具函數
# ============================================================

def get_random_structure(exclude: Optional[List[str]] = None) -> str:
    """
    隨機選擇文章框架

    Args:
        exclude: 要排除的框架 key 列表

    Returns:
        框架 key

    Raises:
        ValueError: 當所有框架都被排除時
    """
    keys = list(ARTICLE_STRUCTURES.keys())
    if exclude:
        keys = [k for k in keys if k not in exclude]
    if not keys:
        raise ValueError("所有框架已被排除，無法選擇")
    chosen = random.choice(keys)
    logger.info(f"[structure_library] 選擇框架: {chosen} ({STRUCTURE_NAMES.get(chosen, '')})")
    return chosen


def get_random_opening(exclude: Optional[List[str]] = None) -> str:
    """
    隨機選擇情境開頭

    Args:
        exclude: 要排除的情境 key 列表

    Returns:
        情境 key
    """
    keys = list(SITUATION_OPENINGS.keys())
    if exclude:
        keys = [k for k in keys if k not in exclude]
    if not keys:
        # 如果全部排除，回退到全部可用
        keys = list(SITUATION_OPENINGS.keys())
    chosen = random.choice(keys)
    logger.info(f"[structure_library] 選擇情境: {chosen} ({SITUATION_NAMES.get(chosen, '')})")
    return chosen


def get_random_sentence_pattern(exclude: Optional[List[str]] = None) -> str:
    """
    隨機選擇句型

    Args:
        exclude: 要排除的句型 key 列表

    Returns:
        句型 key
    """
    keys = list(SENTENCE_PATTERNS.keys())
    if exclude:
        keys = [k for k in keys if k not in exclude]
    if not keys:
        keys = list(SENTENCE_PATTERNS.keys())
    chosen = random.choice(keys)
    logger.info(f"[structure_library] 選擇句型: {chosen} ({SENTENCE_NAMES.get(chosen, '')})")
    return chosen


def render_opening(opening_key: str, **kwargs) -> str:
    """
    渲染情境開頭，將變數替換為實際值

    Args:
        opening_key: 情境 key
        **kwargs: 變數值（company, industry, trend 等）

    Returns:
        渲染後的情境開頭字串
    """
    template = SITUATION_OPENINGS.get(opening_key, "")
    if not template:
        logger.warning(f"[structure_library] 未知的情境: {opening_key}")
        return ""

    # 使用預設值補充缺失的變數
    defaults = SITUATION_DEFAULTS.get(opening_key, {})
    merged_kwargs = {**defaults, **kwargs}

    try:
        result = template.format(**merged_kwargs)
        logger.info(f"[structure_library] 渲染情境 [{opening_key}]: {result}")
        return result
    except KeyError as e:
        logger.warning(f"[structure_library] 情境渲染缺少變數: {e}")
        # 嘗試只使用提供的變數
        try:
            result = template.format(**kwargs)
            return result
        except KeyError:
            logger.error(f"[structure_library] 情境渲染失敗 (缺少必要變數)")
            return kwargs.get("company", "")


def render_sentence(sentence_key: str, **kwargs) -> str:
    """
    渲染句型，將變數替換為實際值

    Args:
        sentence_key: 句型 key
        **kwargs: 變數值

    Returns:
        渲染後的句型字串
    """
    template = SENTENCE_PATTERNS.get(sentence_key, "")
    if not template:
        logger.warning(f"[structure_library] 未知的句型: {sentence_key}")
        return ""

    try:
        result = template.format(**kwargs)
        logger.info(f"[structure_library] 渲染句型 [{sentence_key}]: {result}")
        return result
    except KeyError as e:
        logger.warning(f"[structure_library] 句型渲染缺少變數: {e}")
        return ""


def get_all_structure_keys() -> List[str]:
    """取得所有框架 key 列表"""
    return list(ARTICLE_STRUCTURES.keys())


def get_all_opening_keys() -> List[str]:
    """取得所有情境 key 列表"""
    return list(SITUATION_OPENINGS.keys())


def get_all_sentence_keys() -> List[str]:
    """取得所有句型 key 列表"""
    return list(SENTENCE_PATTERNS.keys())


def get_structure_flow(structure_key: str) -> List[str]:
    """
    取得指定框架的段落流程

    Args:
        structure_key: 框架 key

    Returns:
        段落 key 列表
    """
    return ARTICLE_STRUCTURES.get(structure_key, ARTICLE_STRUCTURES["traditional"])


def get_structure_summary() -> str:
    """取得框架摘要（用於除錯和日誌）"""
    lines = []
    for key, flow in ARTICLE_STRUCTURES.items():
        name = STRUCTURE_NAMES.get(key, key)
        desc = STRUCTURE_DESCRIPTIONS.get(key, "")
        lines.append(f"  - {name} ({key}): {' → '.join(flow)}")
        lines.append(f"    {desc}")
    return "\n".join(lines)
