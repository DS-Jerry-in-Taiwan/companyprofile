"""
Phase 14 Agent F/G: 內容多樣化處理模組

消除模板感，增加生成內容的多樣性和自然度
對應優化項目 #4: 模板感很重 (P1 高優先級)
"""

import random
import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# 多樣化句式庫
INTRO_PATTERNS = [
    # 傳統開頭
    lambda: "",
    # 多樣化開頭
    lambda: "本公司",
    lambda: "本公司為",
    lambda: "本公司主要",
    lambda: "本公司是一家",
    lambda: "我們公司",
    lambda: "我們公司是",
    lambda: "我們公司主要",
    lambda: "我們公司是一家",
    lambda: "該公司",
    lambda: "該企業",
    lambda: "這家公司",
]

# 形容詞庫
ADJECTIVE_POOL = [
    "專業",
    "優質",
    "知名",
    "領先",
    "頂尖",
    "卓越",
    "傑出",
    "著名",
    "經驗豐富",
    "實力堅強",
    "信譽良好",
    "技術先進",
    "規模龐大",
    "創新",
    "可靠",
    "高效",
    "全方位",
    "多元",
    "綜合性",
]

# 行業描述詞庫
INDUSTRY_DESCRIPTORS = [
    "產業",
    "產業領域",
    "業界",
    "同行",
    "市場",
    "相關產業",
    "領域",
    "行業",
    "產業鏈",
]

# 服務模式庫
SERVICE_PATTERNS = [
    "提供",
    "致力於",
    "專精於",
    "專門從事",
    "主要提供",
    "核心業務為",
    "主要業務包括",
    "服務範圍涵蓋",
]

# 常見模板化開頭和表達（需要移除）
TEMPLATE_STARTS = [
    "以下是優化結果：",
    "以下是優化後的公司描述：",
    "以下是生成結果：",
    "公司描述如下：",
    "根據您的要求，",
    "根據以上資訊，",
    "根據提供的信息，",
    "根據您提供的資料，",
    "根據公司資訊，",
    "根據資料顯示，",
    "以下是公司簡介的優化版本：",
    "優化後的內容如下：",
    "生成結果如下：",
    "以下是生成的摘要：",
    "Here is the optimized result:",
    "Based on the information provided,",
    "The company description is as follows:",
]

# 常見模板表達（需要移除）
TEMPLATE_PATTERNS = [
    (r"此外，", ""),
    (r"另外，", ""),
    (r"同時，", ""),
    (r"不僅，", ""),
    (r"而且，", ""),
    (r"同時也，", ""),
    (r"具體來說，", ""),
    (r"詳細而言，", ""),
    (r"不僅提供([^，。]*)，而且提供([^，。]*)", r"提供\1，提供\2"),
    (r"不僅([^，。]*)，而且([^，。]*)", r"\1，\2"),
    (r"不僅([^，。]*)，還([^，。]*)", r"\1，\2"),
    (r"不僅([^，。]*)，也([^，。]*)", r"\1，\2"),
]


def diversify_content(html_content: str) -> str:
    """
    多樣化 HTML 內容，消除模板感

    Args:
        html_content: 原始 HTML 內容

    Returns:
        多樣化後的內容
    """
    if not html_content:
        return html_content

    # 移除模板化開頭
    content = _remove_template_patterns(html_content)

    # 檢查是否包含 HTML 標籤
    has_html = "<" in content and ">" in content

    if has_html:
        content = _diversify_html_content(content)
    else:
        content = _diversify_plain_text(content)

    return content


def _diversify_html_content(html_content: str) -> str:
    """
    多樣化 HTML 內容

    處理邏輯:
    1. 使用 BeautifulSoup 解析 HTML
    2. 遍歷所有文本節點
    3. 對每個文本節點應用多樣化處理（包含模板移除）
    4. 保持 HTML 標籤結構完整
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")

    # 處理所有文本節點
    for text_node in soup.find_all(text=True):
        if text_node.parent.name not in ["script", "style"]:  # 跳過腳本和樣式
            # 先移除模板，再進行其他多樣化處理
            text_without_template = _remove_template_patterns(str(text_node))
            diversified = _diversify_plain_text(text_without_template)
            text_node.replace_with(diversified)

    # 清理空標籤
    for tag in soup.find_all():
        if not tag.get_text(strip=True) and tag.name not in ["br", "hr"]:
            tag.decompose()

    return str(soup)


def _diversify_plain_text(text: str) -> str:
    """
    多樣化純文本內容

    處理順序:
    1. 隨機化句式結構
    2. 隨機化形容詞
    3. 增加表達多樣性
    4. 添加隨機修飾詞
    5. 隨機重組句子（增加多樣性）
    """
    if not text:
        return text

    # 隨機化句式
    text = _randomize_sentence_structures(text)

    # 隨機化形容詞
    text = _randomize_adjectives(text)

    # 增加表達多樣性
    text = _increase_expression_diversity(text)

    # 添加隨機修飾詞（增加多樣性）
    text = _add_random_modifiers(text)

    # 隨機重組句子（增加多樣性）
    text = _reorder_sentences_randomly(text)

    return text


def _randomize_sentence_structures(text: str) -> str:
    """
    隨機化句式結構

    減少固定開頭的使用，增加句式多樣性
    """
    # 定義需要隨機化的固定開頭模式
    fixed_patterns = [
        (
            r"本公司是一家",
            _random_intro("本公司是一家", "本公司", "本公司為", "本公司主要"),
        ),
        (
            r"我們公司是一家",
            _random_intro("我們公司是一家", "我們公司", "我們公司為", "我們公司主要"),
        ),
        (
            r"該公司是一家",
            _random_intro("該公司是一家", "該公司", "該公司為", "該公司主要"),
        ),
        (
            r"本公司主要",
            _random_intro("本公司主要", "本公司", "本公司是一家", "本公司為"),
        ),
        (
            r"我們公司主要",
            _random_intro("我們公司主要", "我們公司", "我們公司是一家", "我們公司為"),
        ),
        (
            r"本公司為",
            _random_intro("本公司為", "本公司", "本公司是一家", "本公司主要"),
        ),
        (
            r"我們公司為",
            _random_intro("我們公司為", "我們公司", "我們公司是一家", "我們公司主要"),
        ),
        (
            r"該公司為",
            _random_intro("該公司為", "該公司", "該公司是一家", "該公司主要"),
        ),
        (r"本公司", _random_intro("本公司", "我們公司", "該公司", "這家公司")),
        (r"我們公司", _random_intro("我們公司", "本公司", "該公司", "這家公司")),
        (r"該公司", _random_intro("該公司", "本公司", "我們公司", "這家公司")),
    ]

    for pattern, replacement in fixed_patterns:
        if random.random() < 0.95:  # 95% 機率隨機化（極高）
            text = re.sub(pattern, replacement, text)

    return text


def _random_intro(*options) -> str:
    """隨機選擇開頭"""
    if not options:
        return ""
    return random.choice(options)


def _random_adj(*options) -> str:
    """隨機選擇形容詞"""
    if not options:
        return ""
    return random.choice(options)


def _random_expr(*options) -> str:
    """隨機選擇表達方式"""
    if not options:
        return ""
    return random.choice(options)


def _add_random_modifiers(text: str) -> str:
    """
    添加隨機修飾詞以增加多樣性

    在適當位置添加副詞、形容詞等修飾詞
    """
    if not text or len(text) < 10:
        return text

    # 隨機修飾詞庫
    modifiers = [
        "非常",
        "極其",
        "相當",
        "十分",
        "格外",
        "特別",
        "尤其",
        "持續",
        "不斷",
        "積極",
        "主動",
        "全面",
        "深入",
        "廣泛",
        "高效",
        "快速",
        "穩定",
        "可靠",
        "安全",
        "靈活",
        "創新",
    ]

    # 隨機決定是否添加修飾詞
    if random.random() < 0.4:  # 40% 機率添加修飾詞
        # 找到合適的位置添加修飾詞
        sentences = re.split(r"[。！？]", text)
        result_sentences = []

        for sentence in sentences:
            if sentence.strip():
                # 隨機決定是否修改這個句子
                if random.random() < 0.3:  # 30% 機率修改這個句子
                    # 在句子開頭或中間添加修飾詞
                    words = sentence.split()
                    if words:
                        # 隨機選擇位置
                        if random.random() < 0.5 and len(words) > 1:
                            # 在第二個詞前添加修飾詞
                            modifier = random.choice(modifiers)
                            words.insert(1, modifier)
                        else:
                            # 在句子開頭添加修飾詞
                            modifier = random.choice(modifiers)
                            words.insert(0, modifier)
                        sentence = " ".join(words)
                result_sentences.append(sentence)

        # 重新組合句子
        text = "。".join(result_sentences) + ("。" if text.endswith("。") else "")

    return text


def _reorder_sentences_randomly(text: str) -> str:
    """
    隨機重組句子以增加多樣性

    對於有多個句子的文本，隨機重新排列句子順序
    """
    if not text or len(text) < 20:
        return text

    # 分割句子
    sentences = re.split(r"([。！？])", text)

    # 將句子和標點配對
    sentence_pairs = []
    for i in range(0, len(sentences) - 1, 2):
        if sentences[i].strip():
            sentence_pairs.append(
                (
                    sentences[i].strip(),
                    sentences[i + 1] if i + 1 < len(sentences) else "",
                )
            )

    # 如果句子太少，不進行重組
    if len(sentence_pairs) < 3:
        return text

    # 隨機決定是否重組句子
    if random.random() < 0.3:  # 30% 機率重組句子
        # 隨機打亂句子順序（保留第一個句子不變）
        first_sentence = sentence_pairs[0]
        other_sentences = sentence_pairs[1:]
        random.shuffle(other_sentences)
        sentence_pairs = [first_sentence] + other_sentences

    # 重新組合句子
    result_parts = []
    for sentence, punctuation in sentence_pairs:
        result_parts.append(sentence + punctuation)

    return "".join(result_parts)

    # 隨機修飾詞庫
    modifiers = [
        "非常",
        "極其",
        "相當",
        "十分",
        "格外",
        "特別",
        "尤其",
        "持續",
        "不斷",
        "積極",
        "主動",
        "全面",
        "深入",
        "廣泛",
        "高效",
        "快速",
        "穩定",
        "可靠",
        "安全",
        "靈活",
        "創新",
    ]

    # 隨機決定是否添加修飾詞
    if random.random() < 0.4:  # 40% 機率添加修飾詞
        # 找到合適的位置添加修飾詞
        sentences = re.split(r"[。！？]", text)
        result_sentences = []

        for sentence in sentences:
            if sentence.strip():
                # 隨機決定是否修改這個句子
                if random.random() < 0.3:  # 30% 機率修改這個句子
                    # 在句子開頭或中間添加修飾詞
                    words = sentence.split()
                    if words:
                        # 隨機選擇位置
                        if random.random() < 0.5 and len(words) > 1:
                            # 在第二個詞前添加修飾詞
                            modifier = random.choice(modifiers)
                            words.insert(1, modifier)
                        else:
                            # 在句子開頭添加修飾詞
                            modifier = random.choice(modifiers)
                            words.insert(0, modifier)
                        sentence = " ".join(words)
                result_sentences.append(sentence)

        # 重新組合句子
        text = "。".join(result_sentences) + ("。" if text.endswith("。") else "")

    return text


def _randomize_adjectives(text: str) -> str:
    """
    隨機化形容詞使用

    避免重複使用相同形容詞
    """
    # 定義常見形容詞模式
    adjective_patterns = [
        (r"專業的", _random_adj("專業", "優質", "頂尖", "卓越")),
        (r"優質的", _random_adj("優質", "專業", "頂尖", "卓越")),
        (r"知名的", _random_adj("知名", "著名", "領先", "傑出")),
        (r"領先的", _random_adj("領先", "頂尖", "卓越", "傑出")),
        (r"頂尖的", _random_adj("頂尖", "領先", "卓越", "專業")),
        (r"卓越的", _random_adj("卓越", "傑出", "頂尖", "領先")),
        (r"傑出的", _random_adj("傑出", "卓越", "頂尖", "領先")),
        (r"著名的", _random_adj("著名", "知名", "領先", "卓越")),
        (r"經驗豐富的", _random_adj("經驗豐富", "資深", "熟練", "專業")),
        (r"資深的", _random_adj("資深", "經驗豐富", "專業", "熟練")),
        (r"先進的", _random_adj("先進", "領先", "創新", "現代化")),
        (r"創新的", _random_adj("創新", "先進", "現代化", "領先")),
    ]

    for old, new in adjective_patterns:
        if random.random() < 0.9:  # 90% 機率隨機化（極高）
            text = re.sub(old, new, text)

    return text


def _increase_expression_diversity(text: str) -> str:
    """
    增加表達多樣性

    替換常見的固定表達方式
    """
    # 替換常見的固定表達
    expression_patterns = [
        (
            r"提供服務",
            _random_expr("提供服務", "提供專業服務", "提供優質服務", "提供全方位服務"),
        ),
        (r"專業服務", _random_expr("專業服務", "優質服務", "頂尖服務", "卓越服務")),
        (r"優質服務", _random_expr("優質服務", "專業服務", "頂尖服務", "卓越服務")),
        (r"技術領先", _random_expr("技術領先", "技術先進", "技術卓越", "技術創新")),
        (r"技術先進", _random_expr("技術先進", "技術領先", "技術創新", "技術卓越")),
        (r"經驗豐富", _random_expr("經驗豐富", "資深經驗", "豐富經驗", "專業經驗")),
        (r"資深經驗", _random_expr("資深經驗", "豐富經驗", "專業經驗", "經驗豐富")),
        (r"軟體開發", _random_expr("軟體開發", "軟體設計", "軟體工程", "應用開發")),
        (r"系統整合", _random_expr("系統整合", "系統集成", "系統開發", "系統實施")),
        (r"移動應用", _random_expr("移動應用", "手機應用", "移動程式", "APP開發")),
        (r"人工智能", _random_expr("人工智能", "AI技術", "智能技術", "機器學習")),
        (r"區塊鏈", _random_expr("區塊鏈", "區塊鏈技術", "分散式帳本", "加密技術")),
    ]

    for old, new in expression_patterns:
        if random.random() < 0.85:  # 85% 機率替換（極高）
            text = re.sub(old, new, text)

    return text


def _remove_template_patterns(text: str) -> str:
    """
    移除模板化表達

    消除明顯的模板痕跡
    """
    if not text:
        return text

    # 移除模板化開頭
    for template in TEMPLATE_STARTS:
        if text.startswith(template):
            text = text[len(template) :]

    # 移除模板化表達（包含在文本中間的）
    for pattern, replacement in TEMPLATE_PATTERNS:
        text = re.sub(pattern, replacement, text)

    # 清理殘留的空白和標點
    text = re.sub(r"^[\s:：,，.。]+", "", text)
    text = re.sub(r"\n\s*\n", "\n", text)

    # 清理多餘的空白
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*，\s*", "，", text)
    text = re.sub(r"\s*。\s*", "。", text)

    return text.strip()


def calculate_diversity_score(content1: str, content2: str) -> float:
    """
    計算兩個內容之間的差異度

    Args:
        content1: 內容1（去除HTML標籤）
        content2: 內容2（去除HTML標籤）

    Returns:
        差異度分數（0-1），越高表示差異越大
    """
    import difflib

    # 移除 HTML 標籤
    text1 = re.sub(r"<[^>]+>", "", content1)
    text2 = re.sub(r"<[^>]+>", "", content2)

    # 計算相似度
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()

    # 返回差異度（1 - 相似度）
    return 1 - similarity


def validate_diversity(
    original_content: str, diversified_content: str, expected_score: float = 0.3
) -> bool:
    """
    驗證內容多樣性

    Args:
        original_content: 原始內容
        diversified_content: 多樣化後的內容
        expected_score: 期望的最低差異度

    Returns:
        是否滿足多樣性要求
    """
    score = calculate_diversity_score(original_content, diversified_content)
    logger.info(f"內容差異度分數: {score:.2f} (期望: {expected_score})")
    return score >= expected_score


def batch_diversify(contents: List[str]) -> List[str]:
    """
    批量多樣化處理

    Args:
        contents: 原始內容列表

    Returns:
        多樣化後的內容列表
    """
    results = []
    for content in contents:
        diversified = diversify_content(content)
        results.append(diversified)

    return results
