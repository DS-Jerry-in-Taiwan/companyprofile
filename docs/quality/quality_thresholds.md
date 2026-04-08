# 質量閾值定義指南

## 問題：什麼時候啟動多源並行？

當前方案：**"如果質量低，才啟動多源並行"**

但這需要明確定義：
1. **質量怎麼評估？**（評分方法）
2. **低質量的閾值是多少？**（具體數字）
3. **在什麼時間點評估？**（流程中的位置）

---

## 方案一：基於搜尋結果質量評估（推薦）

### 評分維度

在搜尋完成後，執行初步質量評估，決定是否需要多源補充。

#### 1. 結果覆蓋度（Coverage Score）

評估搜尋結果是否涵蓋公司的關鍵信息

```python
class SearchQualityEvaluator:
    
    def evaluate_coverage(self, search_result: Dict) -> float:
        """
        評估搜尋結果的覆蓋度 (0-1)
        
        檢查清單：
        - 包含公司名稱？(0.1)
        - 包含業務描述？(0.2)
        - 包含產品/服務？(0.2)
        - 包含成立時間或位置？(0.15)
        - 包含資質認證或榮譽？(0.15)
        - 包含聯繫方式或網址？(0.1)
        - 包含員工規模或營收？(0.1)
        
        總分 = 所有包含項的分數之和
        """
        
        score = 0
        content = search_result.get('answer', '') or \
                  search_result.get('snippet', '')
        
        # 檢查項 1：公司名稱
        if search_result.get('organ') in content:
            score += 0.1
        
        # 檢查項 2：業務描述
        business_keywords = ['業務', '服務', '主要', '提供', '專業', '從事']
        if any(kw in content for kw in business_keywords):
            score += 0.2
        
        # 檢查項 3：產品/服務
        product_keywords = ['產品', '方案', '工具', '平台', '系統', '軟體']
        if any(kw in content for kw in product_keywords):
            score += 0.2
        
        # 檢查項 4：時間或位置
        location_keywords = ['台灣', '成立', '年', '位於', '總部', '地點']
        if any(kw in content for kw in location_keywords):
            score += 0.15
        
        # 檢查項 5：資質或榮譽
        credential_keywords = ['認證', '獲獎', 'ISO', '資格', '榮譽', '獲得']
        if any(kw in content for kw in credential_keywords):
            score += 0.15
        
        # 檢查項 6：聯繫或網址
        contact_keywords = ['電話', '郵件', '網站', '官網', 'http', '@']
        if any(kw in content for kw in contact_keywords):
            score += 0.1
        
        # 檢查項 7：規模或營收
        scale_keywords = ['員工', '人員', '營收', '規模', '資本', '融資']
        if any(kw in content for kw in scale_keywords):
            score += 0.1
        
        return min(score, 1.0)
```

#### 2. 內容相關性（Relevance Score）

評估搜尋結果與查詢的相關程度

```python
def evaluate_relevance(self, query: str, search_result: Dict) -> float:
    """
    評估相關性 (0-1)
    
    基於：
    - 結果標題中有多少查詢詞？
    - 結果摘要中有多少查詢詞？
    - 查詢詞的位置（越前越好）
    """
    
    content = (search_result.get('title', '') + ' ' + 
               search_result.get('snippet', '')).lower()
    query_lower = query.lower()
    
    # 精確匹配：公司全名
    if query_lower in content:
        return 0.95
    
    # 部分匹配：查詢詞出現在前 100 字
    if query_lower in content[:100]:
        return 0.85
    
    # 關鍵詞匹配：至少 80% 的查詢詞出現
    query_words = query_lower.split()
    matched_words = sum(1 for w in query_words if w in content)
    word_match_ratio = matched_words / len(query_words) if query_words else 0
    
    if word_match_ratio >= 0.8:
        return 0.75
    elif word_match_ratio >= 0.6:
        return 0.55
    elif word_match_ratio >= 0.4:
        return 0.35
    else:
        return 0.1
```

#### 3. 內容豐富度（Richness Score）

評估結果的詳細程度

```python
def evaluate_richness(self, search_result: Dict) -> float:
    """
    評估內容豐富度 (0-1)
    
    基於：
    - 文本長度（越長越詳細）
    - 結果數量（有多少個搜尋結果）
    - 是否包含結構化信息（列表、數字等）
    """
    
    content = search_result.get('answer', '') or \
              search_result.get('snippet', '')
    
    # 文本長度評分（0-1）
    # 少於 100 字：0.2，100-300 字：0.5，300+ 字：1.0
    text_length = len(content)
    if text_length < 100:
        length_score = 0.2
    elif text_length < 300:
        length_score = 0.5
    else:
        length_score = 1.0
    
    # 結構化信息評分
    structure_score = 0
    if '<p>' in content or '\n\n' in content:  # 段落
        structure_score += 0.3
    if any(c in content for c in ['•', '-', '1.', '2.']):  # 列表
        structure_score += 0.3
    if any(c.isdigit() for c in content):  # 數字
        structure_score += 0.2
    
    # 結果數量評分
    results = search_result.get('results', [])
    if len(results) >= 3:
        count_score = 1.0
    elif len(results) >= 2:
        count_score = 0.7
    else:
        count_score = 0.3
    
    # 綜合評分
    richness = (length_score * 0.4 + 
                min(structure_score, 1.0) * 0.3 + 
                count_score * 0.3)
    
    return richness
```

### 綜合質量評分

```python
def evaluate_search_quality(self, query: str, search_result: Dict) -> Dict:
    """
    計算綜合質量評分 (0-1)
    
    Returns:
        {
            'overall_score': 0.75,      # 總分
            'coverage_score': 0.8,      # 覆蓋度
            'relevance_score': 0.7,     # 相關性
            'richness_score': 0.75,     # 豐富度
            'need_multi_source': True,  # 是否需要多源
            'reasons': ['內容相關性不足']
        }
    """
    
    coverage = self.evaluate_coverage(search_result)
    relevance = self.evaluate_relevance(query, search_result)
    richness = self.evaluate_richness(search_result)
    
    # 加權平均（可根據實際情況調整權重）
    overall = (
        coverage * 0.4 +      # 覆蓋度最重要
        relevance * 0.35 +    # 相關性次之
        richness * 0.25       # 豐富度最後
    )
    
    # 判定是否需要多源
    need_multi_source = overall < 0.65
    
    reasons = []
    if coverage < 0.5:
        reasons.append("信息覆蓋不足")
    if relevance < 0.5:
        reasons.append("內容相關性低")
    if richness < 0.4:
        reasons.append("內容不夠詳細")
    
    return {
        'overall_score': overall,
        'coverage_score': coverage,
        'relevance_score': relevance,
        'richness_score': richness,
        'need_multi_source': need_multi_source,
        'reasons': reasons
    }
```

---

## 閾值定義

### 推薦的質量閾值

```python
class QualityThreshold:
    """
    質量評估的閾值定義
    """
    
    # 綜合評分閾值
    EXCELLENT = 0.85        # 優秀：立即使用，無需補充
    GOOD = 0.70             # 良好：可用，可選補充
    FAIR = 0.65             # 一般：可用，建議補充
    POOR = 0.50             # 差：需要補充
    VERY_POOR = 0.0         # 很差：必須補充或重新搜尋
    
    # 單項閾值
    MIN_COVERAGE = 0.5      # 最小覆蓋度（5 項以上）
    MIN_RELEVANCE = 0.5     # 最小相關性（至少 50% 匹配）
    MIN_RICHNESS = 0.3      # 最小豐富度（至少 100 字或 2+ 結果）


class AdaptiveStrategy:
    """
    根據質量評分自適應決策
    """
    
    def decide_search_strategy(self, quality_score: float) -> Dict:
        """
        根據質量評分決定下一步策略
        """
        
        if quality_score >= 0.85:
            return {
                'action': 'USE_RESULT',
                'multi_source': False,
                'description': '搜尋質量優秀，直接使用'
            }
        
        elif quality_score >= 0.70:
            return {
                'action': 'USE_WITH_OPTION',
                'multi_source': 'OPTIONAL',
                'description': '搜尋質量良好，可選進行多源補充',
                'probability': 0.3  # 30% 機率觸發多源
            }
        
        elif quality_score >= 0.65:
            return {
                'action': 'USE_WITH_SUPPLEMENT',
                'multi_source': True,
                'description': '搜尋質量一般，建議多源補充',
                'priority': 'MEDIUM'
            }
        
        elif quality_score >= 0.50:
            return {
                'action': 'MUST_SUPPLEMENT',
                'multi_source': True,
                'description': '搜尋質量較差，必須多源補充',
                'priority': 'HIGH'
            }
        
        else:
            return {
                'action': 'RETRY_OR_FALLBACK',
                'multi_source': True,
                'description': '搜尋質量很差，需要重新搜尋或使用備選方案',
                'priority': 'CRITICAL'
            }
```

---

## 實際應用流程

### 在生成流程中的位置

```python
def _generate_brief_traditional(data):
    organ = data["organ"]
    organ_no = data.get("organNo")
    
    # Step 1：初步搜尋（快速、單源）
    logger.info("Step 1: 執行初步搜尋...")
    
    rewriter = QueryRewriter()
    queries = rewriter.rewrite_queries(company_name=organ)
    
    # 使用最有效的第一個查詢
    initial_result = tavily_search(queries[0])
    
    # Step 2：評估質量
    logger.info("Step 2: 評估搜尋質量...")
    
    evaluator = SearchQualityEvaluator()
    quality_assessment = evaluator.evaluate_search_quality(
        query=queries[0],
        search_result=initial_result
    )
    
    logger.info(f"搜尋質量評分：{quality_assessment['overall_score']:.2f}")
    logger.info(f"評估原因：{quality_assessment['reasons']}")
    
    # Step 3：決策
    logger.info("Step 3: 決定搜尋策略...")
    
    decision = AdaptiveStrategy().decide_search_strategy(
        quality_assessment['overall_score']
    )
    
    logger.info(f"決策：{decision['action']}")
    
    # Step 4：根據決策執行後續搜尋
    if decision['multi_source']:
        logger.info("Step 4a: 執行多源並行搜尋...")
        multi_search = MultiSourceSearch()
        search_results = multi_search.parallel_search(queries)
    else:
        logger.info("Step 4b: 使用初步搜尋結果...")
        search_results = [initial_result]
    
    # Step 5：繼續生成流程...
    # ...
```

### 代碼集成示例

```python
# src/functions/utils/generate_brief.py

def _generate_brief_traditional(data):
    organ = data["organ"]
    organ_no = data.get("organNo")
    
    # ===== 新增：質量評估流程 =====
    
    # 初步搜尋
    from ..services.query_rewriter import QueryRewriter
    from ..services.search_quality_evaluator import SearchQualityEvaluator
    from ..services.multi_source_search import MultiSourceSearch
    
    rewriter = QueryRewriter()
    queries = rewriter.rewrite_queries(company_name=organ)
    
    evaluator = SearchQualityEvaluator()
    
    # 用第一個查詢進行初步搜尋
    initial_search = tavily_search(queries[0])
    quality = evaluator.evaluate_search_quality(queries[0], initial_search)
    
    logger.info(f"初步搜尋質量：{quality['overall_score']:.2f}")
    
    # 根據質量決定是否多源
    if quality['overall_score'] < 0.65:
        logger.info("質量低於閾值，執行多源並行搜尋...")
        multi_search = MultiSourceSearch()
        search_results = multi_search.parallel_search(queries)
        
        # 記錄為多源搜尋
        result_source = "multi_source"
    else:
        logger.info("質量滿足要求，使用初步搜尋結果...")
        search_results = [initial_search]
        result_source = "single_source"
    
    # 繼續後續流程...
    clean_text = preprocess_text(search_results[0]['answer'])
    
    prompt = AdvancedPromptBuilder().build_generate_prompt(
        organ=organ,
        organ_no=organ_no,
        search_results=search_results,
        user_brief=data.get("brief")
    )
    
    llm_result = call_llm(prompt)
    result = post_process(llm_result)
    
    # 記錄搜尋策略
    result['search_strategy'] = result_source
    result['quality_assessment'] = quality
    
    return result
```

---

## 具體數值示例

### 示例 1：質量評分 0.85（優秀）

```
公司：Google Taiwan
查詢："Google Taiwan 官網"

評分結果：
├─ 覆蓋度：0.9  ✓
│  ├─ 公司名稱：✓
│  ├─ 業務描述：✓
│  ├─ 產品服務：✓
│  ├─ 成立時間：✓
│  ├─ 資質認證：✓
│  ├─ 聯繫方式：✓
│  └─ 員工規模：✓
├─ 相關性：0.95 ✓
│  └─ 查詢詞精確匹配
├─ 豐富度：0.75 ✓
│  ├─ 文本長度：500+ 字
│  ├─ 結構化信息：有
│  └─ 搜尋結果數：5 個

決策：✓ 使用單源搜尋結果
原因：質量優秀，無需補充
節省成本：80%
```

### 示例 2：質量評分 0.55（差）

```
公司：小型本地新創 XYZ
查詢："XYZ 新創公司"

評分結果：
├─ 覆蓋度：0.4  ✗
│  ├─ 公司名稱：✓
│  ├─ 業務描述：✗
│  ├─ 產品服務：✗
│  ├─ 成立時間：✓
│  ├─ 資質認證：✗
│  ├─ 聯繫方式：✗
│  └─ 員工規模：✗
├─ 相關性：0.6  ✗
│  └─ 關鍵詞部分匹配
├─ 豐富度：0.3  ✗
│  ├─ 文本長度：80 字
│  ├─ 結構化信息：無
│  └─ 搜尋結果數：1 個

決策：⚠ 執行多源並行搜尋
原因：質量低於閾值
成本增加：200%
預期改善：+40%
```

---

## 動態閾值調整

根據實際效果，可動態調整閾值：

```python
class DynamicThreshold:
    """
    根據用戶反饋動態調整質量閾值
    """
    
    def __init__(self):
        self.threshold = 0.65
        self.feedback_history = []
    
    def adjust_threshold(self, feedback: Dict):
        """
        根據反饋調整閾值
        
        feedback 示例：
        {
            'quality_score': 0.60,
            'user_rating': 4,  # 1-5 星
            'helpful': True
        }
        """
        
        self.feedback_history.append(feedback)
        
        # 計算最近 10 個反饋的平均評分
        recent = self.feedback_history[-10:]
        avg_rating = sum(f.get('user_rating', 3) for f in recent) / len(recent)
        
        # 如果平均評分低，降低閾值（啟動多源更頻繁）
        if avg_rating < 3.0:
            self.threshold = max(0.50, self.threshold - 0.05)
            logger.info(f"降低閾值到 {self.threshold:.2f}（質量反饋不佳）")
        
        # 如果平均評分高且成本高，提高閾值（節省成本）
        elif avg_rating > 4.0:
            self.threshold = min(0.75, self.threshold + 0.05)
            logger.info(f"提高閾值到 {self.threshold:.2f}（質量反饋良好）")
```

---

## 推薦值總結

### 簡單版（開發初期）

```python
QUALITY_THRESHOLD = {
    'LOW': 0.60,      # 低於 0.60：必須多源
    'MEDIUM': 0.75,   # 0.60-0.75：可選多源
    'HIGH': 0.85      # 高於 0.85：單源足夠
}

# 決策規則
if quality_score < 0.60:
    use_multi_source = True
else:
    use_multi_source = False
```

### 進階版（優化後）

```python
QUALITY_EVALUATION = {
    # 評分要素
    'coverage_weight': 0.40,
    'relevance_weight': 0.35,
    'richness_weight': 0.25,
    
    # 決策閾值
    'must_supplement': 0.50,      # 質量很差
    'recommend_supplement': 0.65, # 質量一般
    'optional_supplement': 0.75,  # 質量良好
    'sufficient': 0.85,           # 質量優秀
    
    # 單項最小要求
    'min_coverage': 0.40,
    'min_relevance': 0.45,
    'min_richness': 0.25
}
```

---

## 監測和優化

### 記錄關鍵指標

```python
def log_quality_metrics(self, quality_assessment: Dict, 
                       decision: Dict, final_quality: float):
    """
    記錄質量評估指標，用於持續優化
    """
    
    self.logger.info({
        'event': 'quality_assessment',
        'initial_score': quality_assessment['overall_score'],
        'initial_coverage': quality_assessment['coverage_score'],
        'initial_relevance': quality_assessment['relevance_score'],
        'initial_richness': quality_assessment['richness_score'],
        'decision': decision['action'],
        'multi_source_triggered': decision['multi_source'],
        'final_quality': final_quality,  # 生成結果的最終質量
        'cost_multiplier': 1.0 if not decision['multi_source'] else 3.0,
        'timestamp': datetime.now().isoformat()
    })
```

### 分析閾值有效性

每週分析一次：
- 有多少比例的單源結果被評為"不滿意"？
- 有多少比例的多源結果被評為"優秀"？
- 成本與效果的比例是否合理？
- 是否需要調整閾值？

---

## 最終建議

### 開發初期（第 1-2 週）
使用**簡單版**閾值：
```python
if quality_score < 0.65:
    use_multi_source = True
```

### 運行 1 個月後
根據用戶反饋和指標分析，調整閾值到最優值。

### 長期優化
實施動態閾值，根據實時反饋自動調整。

