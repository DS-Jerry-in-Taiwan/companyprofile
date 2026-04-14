"""
Phase 14 Agent F/G: 模板差異化處理模組

確保三個模板（精簡/標準/詳細）有明確的用途和特點
對應優化項目:
- #8: 模板2（精簡版）不夠簡潔
- #10: 三個模板之間差異不明顯

Phase 14 Stage 2 更新:
- 模板風格差異現在由 prompt_builder.py 在 LLM 生成前決定（根本解決方案）
- 此模組只負責後處理：確保長度符合限制（精確截斷）
- 不嘗試改變 LLM 生成的風格，因為後處理無法改變生成風格

Phase 14 Stage 3 更新 (字數限制優化):
- 移除強制截斷邏輯（不再使用 _truncate_html_content 和 _truncate_plain_text 的截斷功能）
- 改為輕量驗證：若字數超出範圍，記錄警告但不強制截斷
- 由 word_count_validator.py 負責字數檢核和重寫觸發
- 若需要嚴格截斷（例如 API 合規性），由調用方決定是否呼叫 truncate 功能
"""

import re
import logging
from typing import Literal, Dict, Any

logger = logging.getLogger(__name__)

# Phase 14 Stage 3 更新：字數範圍（上下限）與檢核模組一致
# 精簡模板特徵
BRIEF_TEMPLATE_FEATURES = {
    "min_length": 40,  # 最小字數
    "max_length": 120,  # 最大字數
    "min_sentences": 1,  # 最少句子數
    "max_sentences": 2,  # 最多句子數
    "allow_line_breaks": False,
    "forbidden_patterns": [
        "此外",
        "另外",
        "同時",
        "此外",
        "不僅",
        "而且",
        "同時也",
        "具體來說",
        "詳細而言",
    ],
    "required_keywords": [],  # 精簡版只需要核心信息
    "style": "concise",  # 簡潔風格
}

# 標準模板特徵
STANDARD_TEMPLATE_FEATURES = {
    "min_length": 130,  # 最小字數
    "max_length": 280,  # 最大字數 (Phase 14 Stage 3: 從 230 放寬至 280)
    "min_sentences": 3,
    "max_sentences": 5,
    "allow_line_breaks": True,
    "forbidden_patterns": [
        "超級",
        "極致",
        "無與倫比",
        "頂級中的頂級",
    ],
    "required_keywords": [
        "成立",
        "服務",
        "特色",
    ],
    "style": "balanced",  # 平衡風格
}

# 詳細模板特徵
DETAILED_TEMPLATE_FEATURES = {
    "min_length": 280,  # 最小字數
    "max_length": 700,  # 最大字數 (Phase 14 Stage 3: 從 550 放寬至 700)
    "min_sentences": 5,
    "max_sentences": 10,
    "allow_line_breaks": True,
    "forbidden_patterns": [],
    "required_keywords": [
        "成立",
        "服務",
        "特色",
        "發展",
        "願景",
        "使命",
    ],
    "style": "detailed",  # 詳細風格
}

TEMPLATE_FEATURES = {
    "brief": BRIEF_TEMPLATE_FEATURES,
    "standard": STANDARD_TEMPLATE_FEATURES,
    "detailed": DETAILED_TEMPLATE_FEATURES,
}


def differentiate_template(
    html_content: str,
    template_type: Literal["brief", "standard", "detailed"] = "standard",
    force_truncate: bool = False,  # Phase 14 Stage 3: 新增參數，預設不強制截斷
) -> str:
    """
    根據模板類型後處理內容（輕量驗證模式）

    Phase 14 Stage 3 更新（字數限制優化）：
    - 預設模式：只做輕量驗證，若字數超出範圍，記錄警告但不強制截斷
    - 由 word_count_validator.py 負責字數檢核和重寫觸發
    - 只有在 force_truncate=True 或內容超過 800 字時才執行截斷

    風格控制：
    - Phase 14 Stage 2 後，模板風格差異由 prompt_builder.py 在 LLM 生成前決定
    - 此函數不嘗試改變風格

    Args:
        html_content: 原始 HTML 內容
        template_type: 模板類型 (brief/standard/detailed)
        force_truncate: 是否強制截斷（預設 False，保持向後相容）

    Returns:
        若 force_truncate=False：原樣返回（僅記錄驗證警告）
        若 force_truncate=True 或內容超過 800 字：截斷後返回
    """
    # Phase 14 Stage 3: 硬截斷門檻
    HARD_TRUNCATE_THRESHOLD = 800  # 只有超過 800 字才截斷

    if not html_content:
        return html_content

    features = TEMPLATE_FEATURES.get(template_type, STANDARD_TEMPLATE_FEATURES)
    min_length = features.get("min_length", 0)
    max_length = features.get("max_length", 200)

    logger.debug(
        f"[template_differentiator] 後處理模板類型: {template_type}，"
        f"字數範圍: {min_length}-{max_length} 字"
    )

    # 計算當前字數
    plain_text = re.sub(r"<[^>]+>", "", html_content)
    current_length = len(plain_text)

    # Phase 14 Stage 3: 輕量驗證模式（預設）
    # 只有當內容超過 HARD_TRUNCATE_THRESHOLD (800) 才截斷
    if not force_truncate:
        if current_length > HARD_TRUNCATE_THRESHOLD:
            # 超過 800 字，執行截斷（截斷到 max_length）
            logger.info(
                f"[template_differentiator] 內容 {current_length} 字超過硬截斷門檻 {HARD_TRUNCATE_THRESHOLD}，"
                f"執行截斷至 {max_length} 字"
            )
            return _apply_length_limit(html_content, features)
        elif current_length > max_length:
            # 超出模板上限但未超過硬截斷門檻，只記錄警告
            logger.warning(
                f"[template_differentiator] 警告：字數 {current_length} 超出上限 {max_length}，"
                f"建議使用 word_count_validator 進行重寫（而非強制截斷）"
            )
        elif current_length < min_length:
            logger.warning(
                f"[template_differentiator] 警告：字數 {current_length} 低於下限 {min_length}，"
                f"建議使用 word_count_validator 進行重寫"
            )
        # 原樣返回
        return html_content

    # 向後相容：force_truncate=True 時執行截斷
    logger.debug(f"[template_differentiator] force_truncate=True，執行截斷")
    result = _apply_length_limit(html_content, features)

    return result


def _differentiate_html_template(html_content: str, features: Dict[str, Any]) -> str:
    """
    差異化處理 HTML 模板

    處理邏輯:
    1. 使用 BeautifulSoup 解析 HTML
    2. 根據模板特徵處理內容
    3. 保持 HTML 標籤結構完整
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")

    # 收集所有文本內容
    all_text = soup.get_text()

    # 根據模板特徵處理
    if features["style"] == "concise":
        # 精簡模板：移除冗餘內容，保留核心
        _simplify_html_content(soup, features)
    elif features["style"] == "detailed":
        # 詳細模板：可以保留更多內容
        # 這裡主要確保不超過長度限制
        pass

    # 轉換回字符串
    result = str(soup)

    # 應用長度限制
    result = _apply_length_limit(result, features)

    return result


def _differentiate_plain_text_template(text: str, features: Dict[str, Any]) -> str:
    """
    差異化處理純文本模板

    處理順序:
    1. 移除冗言內容
    2. 調整內容長度
    3. 移除不適合該模板的內容
    """
    # 移除冗言
    text = _remove_verbose_content(text, features)

    # 調整內容長度
    text = _apply_length_limit(text, features)

    # 移除不適合該模板的內容
    text = _remove_inappropriate_content(text, features)

    return text


def _simplify_html_content(soup, features: Dict[str, Any]):
    """
    簡化 HTML 內容（用於精簡模板）

    移除冗餘的標籤和內容，保留核心信息
    """
    # 移除多餘的段落
    paragraphs = soup.find_all("p")
    if len(paragraphs) > features["max_sentences"]:
        # 只保留前幾個段落
        for p in paragraphs[features["max_sentences"] :]:
            p.decompose()

    # 移除列表項如果太多
    lists = soup.find_all(["ul", "ol"])
    for lst in lists:
        items = lst.find_all("li")
        if len(items) > 3:  # 最多保留3個列表項
            for li in items[3:]:
                li.decompose()

    # 移除包含禁止模式的內容
    for tag in soup.find_all(True):
        try:
            if hasattr(tag, "string") and tag.string:
                tag_text = str(tag.string)
                for pattern in features.get("forbidden_patterns", []):
                    if pattern in tag_text:
                        # 移除整個標籤或簡化內容
                        if features["style"] == "concise":
                            tag.decompose()
                        else:
                            tag.string = tag_text.replace(pattern, "")
        except (TypeError, AttributeError):
            # 跳過無法處理的標籤
            continue


def _remove_verbose_content(text: str, features: Dict[str, Any]) -> str:
    """移除冗言內容"""
    if not text:
        return text

    # 移除禁止的模式
    for pattern in features.get("forbidden_patterns", []):
        text = text.replace(pattern, "")

    # 對於精簡模板，移除過於詳細的描述
    if features["style"] == "concise":
        # 移除列舉性內容
        text = re.sub(r"包括[A-Za-z0-9、，]+等", "", text)
        text = re.sub(r"\d+、", "", text)  # 移除數字列舉
        text = re.sub(r"首先[，,]?其次[，,]?第三", "", text)  # 移除序列詞

    # 清理殘留空白
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _apply_length_limit(text: str, features: Dict[str, Any]) -> str:
    """
    調整內容長度

    確保內容符合模板的字數限制
    """
    max_length = features.get("max_length", 200)

    # 移除 HTML 標籤計算純文字長度
    plain_text = re.sub(r"<[^>]+>", "", text)

    if len(plain_text) <= max_length:
        return text

    # 如果超過限制，需要截斷
    # 對於 HTML 內容，需要更謹慎地處理
    if "<" in text and ">" in text:
        return _truncate_html_content(text, max_length)
    else:
        return _truncate_plain_text(text, max_length)


def _truncate_html_content(html: str, max_length: int) -> str:
    """
    截斷 HTML 內容，保持標籤完整（在自然邊界截斷，不添加 ...）

    Phase 14 Stage 3 更新：
    - 移除 "... " 截斷符號，改為在自然邊界（句號、逗號）截斷
    - 這是向後相容功能，主要用於強制截斷模式
    - 建議使用 word_count_validator 進行重寫而非強制截斷
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    plain_text = soup.get_text()

    if len(plain_text) <= max_length:
        return html

    # 找到自然邊界進行截斷
    # 在句號、逗號處截斷，盡量保持句子完整
    truncated = _find_natural_boundary(html, max_length)

    return truncated


def _truncate_plain_text(text: str, max_length: int) -> str:
    """
    截斷純文本內容（在自然邊界截斷，不添加 ...）

    Phase 14 Stage 3 更新：
    - 移除 "..." 截斷符號，改為在自然邊界截斷
    - 這是向後相容功能，主要用於強制截斷模式
    """
    if len(text) <= max_length:
        return text

    # 找到最後一個完整句子
    sentences = re.split(r"[。！？]", text[:max_length])
    if len(sentences) > 1:
        # 重新組合句子（不包括最後一個不完整的句子）
        result = "".join([s + "。" for s in sentences[:-1]])
        # 移除末尾多餘的句號
        result = result.rstrip("。") + "。"
        return result
    else:
        # 沒有完整句子，在逗號或空白處截斷
        return _find_natural_boundary(text, max_length)


def _find_natural_boundary(text: str, max_length: int) -> str:
    """
    在自然邊界截斷文本，不添加截斷符號

    Phase 14 Stage 3 新增：
    - 找到最後一個合適的斷點（句號、逗號、空白）
    - 確保截斷後語意完整

    Args:
        text: 原始文本
        max_length: 最大長度

    Returns:
        在自然邊界截斷後的文本
    """
    if len(text) <= max_length:
        return text

    # 優先在句號處截斷
    last_period = text.rfind("。", 0, max_length)
    if last_period > max_length * 0.7:  # 句號在合理位置
        return text[: last_period + 1]

    # 次選在逗號處截斷
    last_comma = text.rfind("，", 0, max_length)
    if last_comma > max_length * 0.6:  # 逗號在合理位置
        return text[: last_comma + 1]

    # 第三選在空白處截斷
    last_space = text.rfind(" ", 0, max_length)
    if last_space > max_length * 0.5:
        return text[:last_space]

    # 最後手段：直接截斷
    return text[:max_length]


def _remove_inappropriate_content(text: str, features: Dict[str, Any]) -> str:
    """移除不適合該模板的內容"""
    # 對於精簡模板，移除過於詳細的內容
    if features.get("style") == "concise":
        # 移除詳細的技術描述
        text = re.sub(r"採用[A-Za-z0-9、，]+技術", "採用先進技術", text)
        # 移除過多的形容詞
        text = re.sub(r"非常|極其|特別|十分", "", text)

    # 對於標準模板，保持平衡
    elif features.get("style") == "balanced":
        # 移除誇大的詞語
        text = re.sub(r"世界一流|全球領先|業界第一|極其|超級", "", text)

    return text


def validate_template_differentiation(
    brief_html: str, standard_html: str, detailed_html: str
) -> Dict[str, Any]:
    """
    驗證三個模板的差異化程度

    Args:
        brief_html: 精簡模板輸出
        standard_html: 標準模板輸出
        detailed_html: 詳細模板輸出

    Returns:
        驗證結果字典
    """
    # 移除 HTML 標籤
    brief = re.sub(r"<[^>]+>", "", brief_html)
    standard = re.sub(r"<[^>]+>", "", standard_html)
    detailed = re.sub(r"<[^>]+>", "", detailed_html)

    # 計算字數
    word_counts = {
        "brief": len(brief),
        "standard": len(standard),
        "detailed": len(detailed),
    }

    # 計算句子數
    sentence_counts = {
        "brief": len(re.findall(r"[。！？]", brief)),
        "standard": len(re.findall(r"[。！？]", standard)),
        "detailed": len(re.findall(r"[。！？]", detailed)),
    }

    # 驗證字數差異
    length_valid = (
        word_counts["brief"] < word_counts["standard"] < word_counts["detailed"]
    )

    # 驗證精簡模板簡潔度
    brief_valid = word_counts["brief"] <= BRIEF_TEMPLATE_FEATURES["max_length"]

    # 驗證詳細模板豐富度
    detailed_valid = word_counts["detailed"] > word_counts["standard"]

    # 驗證句子數差異
    sentence_valid = (
        sentence_counts["brief"] <= BRIEF_TEMPLATE_FEATURES["max_sentences"]
        and sentence_counts["standard"] <= STANDARD_TEMPLATE_FEATURES["max_sentences"]
        and sentence_counts["detailed"] >= DETAILED_TEMPLATE_FEATURES["min_sentences"]
    )

    return {
        "word_counts": word_counts,
        "sentence_counts": sentence_counts,
        "length_valid": length_valid,
        "brief_valid": brief_valid,
        "detailed_valid": detailed_valid,
        "sentence_valid": sentence_valid,
        "all_valid": length_valid and brief_valid and detailed_valid and sentence_valid,
    }


def get_template_features(template_type: str) -> Dict[str, Any]:
    """
    取得指定模板的特徵

    Args:
        template_type: 模板類型

    Returns:
        模板特徵字典
    """
    return TEMPLATE_FEATURES.get(template_type, STANDARD_TEMPLATE_FEATURES).copy()
