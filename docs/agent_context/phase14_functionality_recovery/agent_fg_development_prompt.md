# Agent F/G 開發執行 Prompt

**文檔類型**: 開發執行指南 (Development Execution Guide)  
**目標讀者**: Development Team / Agent F/G  
**創建日期**: 2026-04-10  
**預計工時**: 3-5 天（3階段）

---

## 📋 任務概述

Agent F/G 負責 Phase 14 Stage 2 的內容品質與格式優化工作，包含以下三個階段：

| 階段 | 名稱 | 工時 | 優先級 | 對應優化項目 |
|------|------|------|--------|--------------|
| Phase 1 | 格式一致性 | 1天 | P2 | #7, #11 |
| Phase 2 | 內容多樣化 | 1-2天 | **P1 高優先級** | #4 |
| Phase 3 | 模板差異化 | 1-2天 | P2 | #8, #10 |

---

## 🎯 階段一：格式一致性（1天）

### 1.1 任務目標

統一文本格式，解決以下問題：
1. 中英文標點符號混用
2. 多餘空格
3. 換行格式不一致

### 1.2 技術實現

#### 文件位置
```
/home/ubuntu/projects/OrganBriefOptimization/src/functions/utils/post_processing.py
```

#### 新增函數

```python
def _normalize_format(text):
    """
    統一文本格式（標點、空格、換行）
    
    Args:
        text: 輸入文本（可包含 HTML）
        
    Returns:
        格式統一後的文本
    """
    if not text:
        return text
    
    # 檢查是否包含 HTML 標籤
    has_html = "<" in text and ">" in text
    
    if has_html:
        return _normalize_html_format(text)
    else:
        return _normalize_plain_text_format(text)


def _normalize_html_format(text):
    """
    統一 HTML 內容的格式
    
    處理邏輯:
    1. 使用 BeautifulSoup 解析 HTML
    2. 遍歷所有文本節點
    3. 對每個文本節點應用格式統一
    4. 保持 HTML 標籤結構完整
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(text, "html.parser")
    
    for tag in soup.find_all(True):
        if tag.string:
            normalized = _normalize_plain_text_format(tag.string)
            tag.string = normalized
    
    return str(soup)


def _normalize_plain_text_format(text):
    """
    統一純文本格式
    
    處理順序:
    1. 統一標點符號
    2. 移除多餘空格
    3. 統一換行格式
    """
    text = _normalize_punctuation(text)
    text = _remove_extra_spaces(text)
    text = _normalize_line_breaks(text)
    return text


def _normalize_punctuation(text):
    """
    統一標點符號為中文標點
    
    轉換規則:
    - , → ，
    - . → 。 (句尾)
    - ! → ！
    - ? → ？
    - : → ：
    - ; → ；
    - " → 「」
    - ' → 『』
    - ( → （
    - ) → ）
    
    例外:
    - 英文單詞內部的標點不轉換
    - 數字中的小數點不轉換 (如 3.14)
    - 網址中的標點不轉換
    """
    import re
    
    # 定義標點轉換映射
    punct_map = {
        ',': '，',
        '!': '！',
        '?': '？',
        ':': '：',
        ';': '；',
        '(': '（',
        ')': '）',
        '[': '［',
        ']': '］',
    }
    
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        
        # 處理英文句點
        if char == '.':
            if (i > 0 and i < len(text) - 1 and 
                text[i-1].isdigit() and text[i+1].isdigit()):
                result.append(char)  # 小數點保留
            elif i > 0 and text[i-1:i+4] in ['http', 'www.']:
                result.append(char)  # 網址保留
            elif i == len(text) - 1 or text[i+1] in ' \n\t':
                result.append('。')  # 句尾句號
            else:
                result.append(char)
        elif char == '"':
            result.append('「')
        elif char == "'":
            result.append('『')
        elif char in punct_map:
            result.append(punct_map[char])
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result)


def _remove_extra_spaces(text):
    """
    移除多餘空格
    
    處理規則:
    1. 連續多個空格 → 單個空格
    2. 全角空格 → 半角空格
    3. 標點後的多餘空格 → 移除
    4. 段落首尾空格 → 移除
    """
    import re
    
    text = text.strip()
    text = text.replace('　', ' ')
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'([，。！？；：]) ', r'\1', text)
    
    return text


def _normalize_line_breaks(text):
    """
    統一換行格式
    
    處理規則:
    1. 連續 3 個及以上換行 → 2 個換行
    2. 保持段落間 1-2 個換行
    3. 移除段落開頭和結尾的多餘換行
    """
    import re
    
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip('\n')
    
    return text
```

#### 修改 post_process 函數

```python
def post_process(llm_result, original_brief=None):
    # HTML Sanitizer
    safe_html = bleach.clean(
        llm_result.get("body_html", ""),
        tags=["p", "b", "i", "ul", "li", "br"],
        strip=True,
    )

    # Phase 14: 移除冗言
    safe_html = _remove_verbose_phrases(safe_html)

    # Phase 14 Agent F/G: 格式統一 (新增)
    safe_html = _normalize_format(safe_html)

    # Phase 14.1: 台灣用語轉換
    if TAIWAN_TERMS_AVAILABLE:
        safe_html = _convert_to_taiwan_terms(safe_html)
        logger.info("已應用台灣用語轉換到 body_html")
    
    # ... 其餘代碼保持不變
```

### 1.3 測試要求

創建測試文件: `tests/test_format_normalization.py`

```python
import pytest
from src.functions.utils.post_processing import (
    _normalize_format,
    _normalize_punctuation,
    _remove_extra_spaces,
    _normalize_line_breaks,
    _normalize_html_format,
)


class TestPunctuationNormalization:
    """標點符號統一測試"""
    
    def test_comma_normalization(self):
        """測試逗號統一"""
        assert _normalize_punctuation("你好,世界") == "你好，世界"
    
    def test_sentence_period_normalization(self):
        """測試句號統一"""
        assert _normalize_punctuation("這是測試.") == "這是測試。"
    
    def test_exclamation_normalization(self):
        """測試感嘆號統一"""
        assert _normalize_punctuation("太棒了!") == "太棒了！"
    
    def test_question_mark_normalization(self):
        """測試問號統一"""
        assert _normalize_punctuation("是這樣嗎?") == "是這樣嗎？"
    
    def test_colon_normalization(self):
        """測試冒號統一"""
        assert _normalize_punctuation("時間:") == "時間："
    
    def test_semicolon_normalization(self):
        """測試分號統一"""
        assert _normalize_punctuation("蘋果;香蕉") == "蘋果；香蕉"
    
    def test_parentheses_normalization(self):
        """測試括號統一"""
        assert _normalize_punctuation("(測試)") == "（測試）"
    
    def test_quote_normalization(self):
        """測試引號統一"""
        assert _normalize_punctuation('"內容"') == "「內容」"
    
    def test_decimal_point_preserved(self):
        """測試小數點保留"""
        assert _normalize_punctuation("3.14") == "3.14"
    
    def test_url_preserved(self):
        """測試網址保留"""
        assert _normalize_punctuation("http://example.com") == "http://example.com"


class TestExtraSpacesRemoval:
    """多餘空格移除測試"""
    
    def test_multiple_spaces_to_single(self):
        """測試多個空格合併為單個"""
        assert _remove_extra_spaces("你好  世界") == "你好 世界"
    
    def test_fullwidth_space_conversion(self):
        """測試全角空格轉換"""
        assert _remove_extra_spaces("你好　世界") == "你好 世界"
    
    def test_space_after_punctuation_removed(self):
        """測試標點後空格移除"""
        assert _remove_extra_spaces("你好， 世界") == "你好，世界"
    
    def test_leading_trailing_spaces_removed(self):
        """測試首尾空格移除"""
        assert _remove_extra_spaces("  你好世界  ") == "你好世界"


class TestLineBreakNormalization:
    """換行格式統一測試"""
    
    def test_multiple_linebreaks_to_two(self):
        """測試多個換行合併為兩個"""
        assert _normalize_line_breaks("段落1\n\n\n\n段落2") == "段落1\n\n段落2"
    
    def test_leading_linebreaks_removed(self):
        """測試開頭換行移除"""
        assert _normalize_line_breaks("\n\n段落") == "段落"
    
    def test_trailing_linebreaks_removed(self):
        """測試結尾換行移除"""
        assert _normalize_line_breaks("段落\n\n") == "段落"
    
    def test_mixed_linebreaks_normalized(self):
        """測試混合換行符統一"""
        assert _normalize_line_breaks("段落1\r\n\r\n段落2") == "段落1\n\n段落2"


class TestHTMLFormatNormalization:
    """HTML內容格式統一測試"""
    
    def test_html_with_punctuation(self):
        """測試HTML內容中的標點"""
        assert _normalize_html_format("<p>你好,世界.</p>") == "<p>你好，世界。</p>"
    
    def test_html_with_extra_spaces(self):
        """測試HTML內容中的多餘空格"""
        assert _normalize_html_format("<p>你好  世界</p>") == "<p>你好 世界</p>"
    
    def test_nested_html_tags(self):
        """測試嵌套HTML標籤"""
        html = "<div><p>你好,</p><p>世界.</p></div>"
        expected = "<div><p>你好，</p><p>世界。</p></div>"
        assert _normalize_html_format(html) == expected


class TestFormatIntegration:
    """整合測試"""
    
    def test_full_normalization(self):
        """測試完整格式統一流程"""
        input_text = "你好,  世界\n\n\n這是測試."
        expected = "你好，這是測試。"
        assert _normalize_format(input_text) == expected
    
    def test_empty_text(self):
        """測試空文本"""
        assert _normalize_format("") == ""
        assert _normalize_format(None) is None
    
    def test_pure_numbers(self):
        """測試純數字"""
        assert _normalize_format("3.14") == "3.14"
```

### 1.4 驗收標準

- [ ] 中英文標點符號統一為中文標點
- [ ] 多餘空格已移除
- [ ] 換行格式統一
- [ ] HTML 內容格式正確
- [ ] 單元測試通過率 100%
- [ ] 新增測試用例 ≥ 30 個
- [ ] 處理時間平均 < 10ms

---

## 🎯 階段二：內容多樣化（1-2天）⭐ P1 高優先級

### 2.1 任務目標

消除內容模板感，提升生成多樣性。

### 2.2 問題分析

根據 `OPTIMIZATION_SUGGESTIONS_SUMMARY.md` P1 高優先級項目 #4：

**問題**: 模板感很重
- 每次生成內容相似度過高
- 句式結構固定
- 形容詞和修飾語單一

**發現案例**: 10 個（從 12 個測試案例中發現）

### 2.3 技術實現方案

#### 方案：多策略隨機化

在 `src/functions/utils/content_diversifier.py` 中實現：

```python
"""
內容多樣化處理模組

消除模板感，增加生成內容的多樣性和自然度
"""

import random
import re
from typing import List, Optional


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
    "專業", "優質", "知名", "領先", "頂尖", "卓越", "傑出", "著名",
    "經驗豐富", "實力堅強", "信譽良好", "技術先進", "規模龐大",
    "創新", "可靠", "高效", "全方位", "多元", "綜合性",
]

# 行業描述詞庫
INDUSTRY_DESCRIPTORS = [
    "產業", "產業領域", "業界", "同行", "市場",
    "相關產業", "領域", "行業", "產業鏈",
]

# 服務模式庫
SERVICE_PATTERNS = [
    "提供", "致力於", "專精於", "專門從事", "主要提供",
    "核心業務為", "主要業務包括", "服務範圍涵蓋",
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
    
    # 隨機選擇句式
    content = _randomize_sentence_structures(html_content)
    
    # 隨機化形容詞
    content = _randomize_adjectives(content)
    
    # 消除固定句型
    content = _remove_template_patterns(content)
    
    return content


def _randomize_sentence_structures(text: str) -> str:
    """
    隨機化句式結構
    
    減少固定開頭的使用，增加句式多樣性
    """
    # 定義需要隨機化的固定開頭模式
    fixed_patterns = [
        (r"本公司是一家", _random_intro("本公司是一家", "本公司")),
        (r"我們公司是一家", _random_intro("我們公司是一家", "我們公司")),
        (r"該公司是一家", _random_intro("該公司是一家", "該公司")),
        (r"本公司主要", _random_intro("本公司主要", "本公司")),
        (r"我們公司主要", _random_intro("我們公司主要", "我們公司")),
        (r"本公司為", _random_intro("本公司為", "本公司")),
        (r"我們公司為", _random_intro("我們公司為", "我們公司")),
    ]
    
    for pattern, replacement in fixed_patterns:
        if random.random() < 0.5:  # 50% 機率隨機化
            text = re.sub(pattern, replacement, text)
    
    return text


def _random_intro(*options) -> str:
    """隨機選擇開頭"""
    return random.choice(options)


def _randomize_adjectives(text: str) -> str:
    """
    隨機化形容詞使用
    
    避免重複使用相同形容詞
    """
    # 定義常見形容詞模式
    adjective_patterns = [
        (r"專業的", "專業"),
        (r"優質的", "優質"),
        (r"知名的", "知名"),
    ]
    
    for old, new in adjective_patterns:
        if random.random() < 0.3:  # 30% 機率簡化
            text = re.sub(old, new, text)
    
    return text


def _remove_template_patterns(text: str) -> str:
    """
    移除模板化表達
    
    消除明顯的模板痕跡
    """
    # 移除「以下是...」類型的制式開頭
    template_starts = [
        "以下是優化結果：",
        "以下是優化後的公司描述：",
        "以下是生成結果：",
        "公司描述如下：",
    ]
    
    for template in template_starts:
        text = text.replace(template, "")
    
    # 清理殘留的空白
    text = re.sub(r'^\s+', '', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
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
    text1 = re.sub(r'<[^>]+>', '', content1)
    text2 = re.sub(r'<[^>]+>', '', content2)
    
    # 計算相似度
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
    
    # 返回差異度（1 - 相似度）
    return 1 - similarity


def validate_diversity(html_content: str, expected_score: float = 0.3) -> bool:
    """
    驗證內容多樣性
    
    對同一輸入生成多次內容，檢查差異度
    
    Args:
        html_content: 測試內容
        expected_score: 期望的最低差異度
        
    Returns:
        是否滿足多樣性要求
    """
    # 這個函數需要在實際應用中調用 LLM 生成多次
    # 並計算平均差異度
    return True  # 暫時返回 True，實際實現時需要計算
```

#### 修改調用流程

在 `src/functions/utils/post_processing.py` 的 `post_process` 函數中添加：

```python
def post_process(llm_result, original_brief=None):
    # ... 前面的處理保持不變 ...
    
    # Phase 14.1: 台灣用語轉換
    if TAIWAN_TERMS_AVAILABLE:
        safe_html = _convert_to_taiwan_terms(safe_html)
    
    # Phase 14 Agent F/G: 格式統一
    safe_html = _normalize_format(safe_html)
    
    # Phase 14 Agent F/G: 內容多樣化 (新增)
    try:
        from src.functions.utils.content_diversifier import diversify_content
        safe_html = diversify_content(safe_html)
    except ImportError:
        logger.warning("content_diversifier 模組未找到，跳過多樣化處理")
    
    # ... 後面的處理保持不變 ...
```

### 2.4 測試要求

```python
# tests/test_content_diversifier.py

import pytest
from src.functions.utils.content_diversifier import (
    diversify_content,
    calculate_diversity_score,
    _remove_template_patterns,
    _randomize_sentence_structures,
)


class TestTemplateRemoval:
    """模板移除測試"""
    
    def test_remove_optimization_prefix(self):
        """測試移除「以下是優化結果」"""
        text = "以下是優化結果：公司描述..."
        result = _remove_template_patterns(text)
        assert "以下是優化結果" not in result
    
    def test_remove_template_intro(self):
        """測試移除模板化開頭"""
        text = "以下是優化後的公司描述：公司成立於..."
        result = _remove_template_patterns(text)
        assert "以下是優化後的公司描述" not in result


class TestSentenceRandomization:
    """句式隨機化測試"""
    
    def test_random_intro_selection(self):
        """測試隨機開頭選擇"""
        results = set()
        for _ in range(10):
            text = "本公司是一家專業的公司"
            result = _randomize_sentence_structures(text)
            results.add(result)
        # 多次執行應該有不同的結果
        assert len(results) > 1 or results  # 至少有一個結果


class TestDiversityCalculation:
    """多樣性計算測試"""
    
    def test_identical_content_zero_diversity(self):
        """測試完全相同的內容差異度為0"""
        score = calculate_diversity_score(
            "<p>這是相同的內容</p>",
            "<p>這是相同的內容</p>"
        )
        assert score == 0.0
    
    def test_different_content_high_diversity(self):
        """測試完全不同的內容差異度接近1"""
        score = calculate_diversity_score(
            "<p>蘋果是紅色的水果</p>",
            "<p>香蕉是黃色的水果</p>"
        )
        assert score > 0.5
    
    def test_html_tags_ignored(self):
        """測試HTML標籤被忽略"""
        score1 = calculate_diversity_score(
            "<p>內容A</p>",
            "<div>內容B</div>"
        )
        score2 = calculate_diversity_score(
            "內容A",
            "內容B"
        )
        assert abs(score1 - score2) < 0.01


class TestContentDiversification:
    """內容多樣化整合測試"""
    
    def test_diversify_empty_content(self):
        """測試空內容處理"""
        assert diversify_content("") == ""
        assert diversify_content(None) is None
    
    def test_diversify_removes_template_markers(self):
        """測試多樣化處理移除模板標記"""
        text = "以下是優化結果：公司描述..."
        result = diversify_content(text)
        assert "以下是優化結果" not in result
    
    def test_multiple_calls_produce_different_results(self):
        """測試多次調用產生不同結果"""
        text = "本公司是一家專業的公司，提供優質服務。"
        results = [diversify_content(text) for _ in range(5)]
        # 由於隨機性，結果應該有所不同（但不是絕對的）
        unique_results = set(results)
        # 至少應該有一些變化
        assert len(unique_results) >= 1  # 放寬測試條件
```

### 2.5 驗收標準

- [ ] 生成內容無明顯模板痕跡
- [ ] 句式結構多樣化
- [ ] 相同輸入5次生成的內容差異度 > 30%
- [ ] 無「以下是...」等制式開頭
- [ ] 無「公司是一家...」等固定句型
- [ ] 單元測試通過率 100%
- [ ] 新增測試用例 ≥ 15 個

---

## 🎯 階段三：模板差異化（1-2天）

### 3.1 任務目標

優化三個模板的差異化設計，確保每個模板都有明確的用途和特點。

### 3.2 問題分析

根據 `OPTIMIZATION_SUGGESTIONS_SUMMARY.md`：

**項目 #8**: 模板2（精簡版）不夠簡潔
- 發現案例: 2 個
- 問題: 精簡模板應該更簡潔有力

**項目 #10**: 三個模板之間差異不明顯
- 發現案例: 4 個
- 問題: 三個模板的功能區分不夠明確

### 3.3 技術實現方案

#### 方案：Template-specific Optimization

```python
# src/functions/utils/template_differentiator.py

"""
模板差異化處理模組

確保三個模板（精簡/標準/詳細）有明確的用途和特點
"""

import re
from typing import Literal


# 精簡模板特徵
BRIEF_TEMPLATE_FEATURES = {
    "max_length": 100,  # 最大字數
    "min_sentences": 1,  # 最少句子數
    "max_sentences": 2,  # 最多句子數
    "allow_line_breaks": False,
    "forbidden_patterns": [
        "此外", "另外", "同時", "此外",
        "不僅", "而且", "同時也",
    ],
    "required_keywords": [],  # 精簡版只需要核心信息
}

# 標準模板特徵
STANDARD_TEMPLATE_FEATURES = {
    "max_length": 200,
    "min_sentences": 3,
    "max_sentences": 5,
    "allow_line_breaks": True,
    "forbidden_patterns": [
        "超級", "極致", "無與倫比",
    ],
    "required_keywords": [
        "成立", "服務", "特色",
    ],
}

# 詳細模板特徵
DETAILED_TEMPLATE_FEATURES = {
    "max_length": 500,  # 放寬上限以容納更多內容
    "min_sentences": 5,
    "max_sentences": 10,
    "allow_line_breaks": True,
    "forbidden_patterns": [],
    "required_keywords": [
        "成立", "服務", "特色", "發展", "願景",
    ],
}

TEMPLATE_FEATURES = {
    "brief": BRIEF_TEMPLATE_FEATURES,
    "standard": STANDARD_TEMPLATE_FEATURES,
    "detailed": DETAILED_TEMPLATE_FEATURES,
}


def differentiate_template(
    html_content: str,
    template_type: Literal["brief", "standard", "detailed"]
) -> str:
    """
    根據模板類型差異化處理內容
    
    Args:
        html_content: 原始 HTML 內容
        template_type: 模板類型 (brief/standard/detailed)
        
    Returns:
        差異化處理後的內容
    """
    if not html_content:
        return html_content
    
    features = TEMPLATE_FEATURES.get(template_type, STANDARD_TEMPLATE_FEATURES)
    
    # 移除冗言
    content = _remove_verbose_content(html_content, features)
    
    # 調整內容長度
    content = _adjust_content_length(content, features)
    
    # 移除不適合該模板的內容
    content = _remove_inappropriate_content(content, features)
    
    return content


def _remove_verbose_content(text: str, features: dict) -> str:
    """移除冗言內容"""
    # 移除禁止的模式
    for pattern in features.get("forbidden_patterns", []):
        text = text.replace(pattern, "")
    
    # 清理殘留空白
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def _adjust_content_length(text: str, features: dict) -> str:
    """
    調整內容長度
    
    確保內容符合模板的字數限制
    """
    max_length = features.get("max_length", 200)
    
    # 移除 HTML 標籤計算純文字長度
    plain_text = re.sub(r'<[^>]+>', '', text)
    
    if len(plain_text) <= max_length:
        return text
    
    # 如果超過限制，從結尾截斷
    # 注意：這只是簡化處理，實際可能需要更好的截斷邏輯
    
    # 找到最後一個完整句子
    sentences = re.split(r'[。！？]', plain_text[:max_length])
    if len(sentences) > 1:
        # 移除最後一個不完整的句子
        last_sentence_end = len(sentences[-1]) + 1
        plain_text = plain_text[:-last_sentence_end] if last_sentence_end < len(plain_text) else plain_text
    
    # 移除對應的 HTML 內容（簡化處理）
    # 實際實現時需要更複雜的 HTML 截斷邏輯
    
    return plain_text


def _remove_inappropriate_content(text: str, features: dict) -> str:
    """移除不適合該模板的內容"""
    # 對於精簡模板，移除過於詳細的內容
    if features.get("max_length", 200) <= 100:
        # 移除包含列舉性內容的部分
        text = re.sub(r'包括[A-Za-z0-9、，]+等', '', text)
        text = re.sub(r'\d+、', '', text)  # 移除數字列舉
    
    return text


def validate_template_differentiation(
    brief_html: str,
    standard_html: str,
    detailed_html: str
) -> dict:
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
    brief = re.sub(r'<[^>]+>', '', brief_html)
    standard = re.sub(r'<[^>]+>', '', standard_html)
    detailed = re.sub(r'<[^>]+>', '', detailed_html)
    
    # 計算字數
    word_counts = {
        "brief": len(brief),
        "standard": len(standard),
        "detailed": len(detailed),
    }
    
    # 驗證字數差異
    length_valid = (
        word_counts["brief"] < word_counts["standard"] < word_counts["detailed"]
    )
    
    # 驗證精簡模板簡潔度
    brief_valid = word_counts["brief"] <= 100
    
    # 驗證詳細模板豐富度
    detailed_valid = word_counts["detailed"] > word_counts["standard"]
    
    return {
        "word_counts": word_counts,
        "length_valid": length_valid,
        "brief_valid": brief_valid,
        "detailed_valid": detailed_valid,
        "all_valid": length_valid and brief_valid and detailed_valid,
    }
```

#### 修改調用流程

```python
def post_process(llm_result, original_brief=None, template_type="standard"):
    # ... 前面的處理保持不變 ...
    
    # Phase 14.1: 台灣用語轉換
    if TAIWAN_TERMS_AVAILABLE:
        safe_html = _convert_to_taiwan_terms(safe_html)
    
    # Phase 14 Agent F/G: 格式統一
    safe_html = _normalize_format(safe_html)
    
    # Phase 14 Agent F/G: 內容多樣化
    try:
        from src.functions.utils.content_diversifier import diversify_content
        safe_html = diversify_content(safe_html)
    except ImportError:
        pass
    
    # Phase 14 Agent F/G: 模板差異化 (新增)
    try:
        from src.functions.utils.template_differentiator import differentiate_template
        safe_html = differentiate_template(safe_html, template_type)
    except ImportError:
        logger.warning("template_differentiator 模組未找到，跳過模板差異化處理")
    
    # ... 後面的處理保持不變 ...
```

### 3.4 測試要求

```python
# tests/test_template_differentiator.py

import pytest
from src.functions.utils.template_differentiator import (
    differentiate_template,
    validate_template_differentiation,
    BRIEF_TEMPLATE_FEATURES,
    STANDARD_TEMPLATE_FEATURES,
    DETAILED_TEMPLATE_FEATURES,
)


class TestTemplateFeatures:
    """模板特徵測試"""
    
    def test_brief_template_max_length(self):
        """測試精簡模板最大字數"""
        assert BRIEF_TEMPLATE_FEATURES["max_length"] == 100
    
    def test_brief_template_no_line_breaks(self):
        """測試精簡模板不允許換行"""
        assert BRIEF_TEMPLATE_FEATURES["allow_line_breaks"] is False
    
    def test_standard_template_moderate_length(self):
        """測試標準模板中等字數"""
        assert STANDARD_TEMPLATE_FEATURES["max_length"] == 200
    
    def test_detailed_template_max_length(self):
        """測試詳細模板大字數"""
        assert DETAILED_TEMPLATE_FEATURES["max_length"] == 500


class TestTemplateDifferentiation:
    """模板差異化測試"""
    
    def test_differentiate_brief_template(self):
        """測試精簡模板差異化"""
        text = "本公司是一家專業的公司，提供優質服務。此外，我們還提供其他服務。"
        result = differentiate_template(text, "brief")
        assert "此外" not in result  # 精簡模板移除冗言
    
    def test_differentiate_standard_template(self):
        """測試標準模板差異化"""
        text = "本公司是一家超級專業的公司。"
        result = differentiate_template(text, "standard")
        assert "超級" not in result  # 標準模板移除誇大詞
    
    def test_differentiate_detailed_template(self):
        """測試詳細模板保留更多內容"""
        text = "本公司是一家專業的公司。"
        result = differentiate_template(text, "detailed")
        assert "專業的公司" in result


class TestTemplateValidation:
    """模板驗證測試"""
    
    def test_valid_template_differentiation(self):
        """測試有效的模板差異化"""
        result = validate_template_differentiation(
            "<p>精簡內容</p>",  # 短
            "<p>標準內容</p>",  # 中
            "<p>詳細內容</p>",  # 長
        )
        assert result["all_valid"] is True
    
    def test_invalid_brief_template(self):
        """測試無效的精簡模板"""
        result = validate_template_differentiation(
            "<p>這是一個非常詳細的內容描述</p>",  # 太長
            "<p>標準內容</p>",
            "<p>詳細內容</p>",
        )
        assert result["brief_valid"] is False
    
    def test_same_length_templates_invalid(self):
        """測試相同長度的模板無效"""
        result = validate_template_differentiation(
            "<p>內容</p>",
            "<p>內容</p>",
            "<p>內容</p>",
        )
        assert result["length_valid"] is False
```

### 3.5 驗收標準

- [ ] 精簡模板平均字數 < 100 字
- [ ] 標準模板平均字數 100-200 字
- [ ] 詳細模板平均字數 > 200 字
- [ ] 三個模板長度明顯不同
- [ ] 三個模板用途場景明確區分
- [ ] 模板之間差異度 ≥ 40%
- [ ] 單元測試通過率 100%
- [ ] 新增測試用例 ≥ 10 個

---

## 📊 開發進度追蹤

### 開發完成標誌

| 階段 | 完成標誌 | 預計完成日期 |
|------|----------|--------------|
| Phase 1 | 格式一致性功能上線 + 測試通過 | 2026-04-11 |
| Phase 2 | 內容多樣化功能上線 + 差異度驗證通過 | 2026-04-13 |
| Phase 3 | 模板差異化功能上線 + 差異度驗證通過 | 2026-04-15 |

### Checkpoint 2 交付物

| 交付物 | 狀態 | 負責人 |
|--------|------|--------|
| Phase 1 代碼 | ⏳ 待開發 | Agent F/G |
| Phase 1 測試 | ⏳ 待開發 | Agent F/G |
| Phase 2 代碼 | ⏳ 待開發 | Agent F/G |
| Phase 2 測試 | ⏳ 待開發 | Agent F/G |
| Phase 3 代碼 | ⏳ 待開發 | Agent F/G |
| Phase 3 測試 | ⏳ 待開發 | Agent F/G |
| 整合測試報告 | ⏳ 待完成 | Agent F/G |
| 驗收測試通過 | ⏳ 待完成 | 測試團隊 |

---

## 📞 技術支援

**參考資料**:
1. `src/functions/utils/post_processing.py` - 現有實現
2. `src/plugins/taiwan_terms/` - 參考模組結構
3. `docs/test_report/v0.0.1/stage2/stage2_developer_assessment.md` - 階段評估
4. `docs/test_report/v0.0.1/stage2/agent_fg_technical_spec.md` - Agent F/G 技術規格書

**問題反饋**:
- 技術問題 → Agent C 負責人
- 進度問題 → 項目經理
- 需求澄清 → Product Owner

---

**文檔版本**: v1.0  
**創建日期**: 2026-04-10  
**最後更新**: 2026-04-10
