# Phase 23 Developer Prompt

## 任務
實作模板多樣化功能，解決「模板過於一致」與「句型僵化」問題。

## 依據文件
- 規劃概覽: `docs/agent_context/phase23/DEVELOPMENT_PLAN.md`
- 詳細實作: `docs/agent_context/phase23/DEVELOPMENT_PLAN_DETAIL.md`
- 測試指標: `docs/agent_context/phase23/TEST_METRICS.md`
- 任務邊界: `docs/agent_context/phase23/TASK_BOUNDARIES.md`
- 開發日誌: `docs/agent_context/phase23/DEVELOPMENT_LOG.md`

## 三個庫（核心目標）

| 庫 | 用途 | 數量 |
|------|------|------|
| **文章框架庫** | 段落順序多樣化 | 6 種 |
| **情境庫** | 開頭情境描述 | 5 種 |
| **句型庫** | 句型多樣化 | 5+ 種 |

### 文章框架庫內容

| 框架 | 結構 | 適用場景 |
|------|------|----------|
| 傳統結構| 成立→理念→服務→競爭力→未來 | 大眾、傳產 |
| 服務優先| 服務核心→成立→特色→未來 | 服務業 |
| 價值優先| 核心價值→成立→服務→未來 | 品牌導向 |
| 未來導向| 願景→成立→核心→服務 | 新創、科技 |
| 特色優先| 核心特色→成立→服務→未來 | 差異化公司 |
| 數據導向| 資本/規模→成立→核心→未來 | 上市公司 |

### 情境庫內容

| 類型 | 結構 | 範例 |
|------|------|------|
| 產業情境 | 「在[產業]...[公司]...」 | 在AI快速發展的時代... |
| 市場情境 | 「面對[趨勢]...[公司]...」 | 面對數位轉型浪潮... |
| 問題情境 | 「針對[痛點]...[公司]...」 | 針對企業尋才困難... |
| 趨勢情境 | 「隨著[趨勢]...[公司]...」 | 隨著環保意識抬頭... |
| 使用者情境 | 「當你需要[服務]...[公司]...」 | 當你需要專業會計服務時... |

### 句型庫內容

| 類型 | 結構 | 範例 |
|------|------|------|
| 服務導向 | 「專注於[產業]的[公司]，提供...」 | 常用 |
| 特色導向 | 「以[特色]聞名的[公司]...」 | 品牌 |
| 數據導向 | 「擁有[年數]年歷史的[公司]...」 | 資訊多 |
| 問句式 | ��想找[服務]嗎？[公司]是...」 | 導購 |
| 情境描述 | 「[情境]，[公司]...」 | 氛圍 |

---

## 實作步驟

### Phase 23a: Prompt 更新（一定要做）

#### Step 1: 修改 generate_prompt_template.txt
修改 `src/functions/generate_prompt_template.txt`，加入多樣化撰寫原則：

```
## 撰寫原則
1. 開頭多樣化
   - 不要使用「[公司]成立於[年份]年」的固定格式
   - 優先以「核心服務/產品特色」開頭
   - 可以使用情境描述、問句、產業趨勢等多元開頭
2. 段落結構多樣化
   - 不一定要按「成立→理念→服務→競爭力→未來」的順序
   - 可以根據公司特色調整段落優先順序
3. 句型變化
   - 避免重複使用相同句型
```

**驗證**：確認 Prompt 包含多樣化原則

#### Step 2: 修改 optimize_prompt_template.txt
同步修改 `src/functions/optimize_prompt_template.txt`，加入相同原則

**驗證**：兩份 Prompt 原則一致

#### Step 3: 整合測試（Prompt）
執行生成測試，驗證開頭是否多樣化

**驗證**：
- 固定格式開頭率 < 20%
- 開頭句型種類 >= 3 種

---

### Phase 23b: 模板庫實作

#### Step 4: 建立文章框架庫
建立 `src/functions/utils/structure_library.py`，定義文章框架：

```python
ARTICLE_STRUCTURES = {
    "traditional": ["foundation", "core", "vibe", "future"],
    "service_first": ["core", "foundation", "vibe", "future"],
    "value_first": ["core_values", "foundation", "core", "future"],
    "future_oriented": ["future", "foundation", "core", "vibe"],
    "feature_first": ["core_features", "foundation", "core", "future"],
    "data_oriented": ["scale", "foundation", "core", "future"],
}
```

**驗證**：
- 框架種類 >= 6
- 單元測試通過

#### Step 5: 建立情境庫
在 `structure_library.py` 加入情境開頭：

```python
SITUATION_OPENINGS = {
    "industry": "在{industry}領域，{company}...",
    "market": "面對{trend}，{company}...",
    "problem": "針對{challenge}，{company}...",
    "trend": "隨著{trend}，{company}...",
    "user": "當你需要{service}，{company}...",
}
```

**驗證**：
- 情境種類 >= 5
- 變數替換正確

#### Step 6: 建立句型庫
在 `structure_library.py` 加入句型：

```python
SENTENCE_PATTERNS = {
    "service": "專注於{industry}的{company}，提供{service}。",
    "feature": "以{feature}聞名的{company}，{action}。",
    "data": "擁有{years}年歷史的{company}，{description}。",
    "question": "想找{service}嗎？{company}是您的最佳選擇。",
    "situation": "{situation}，{company}{action}。",
}
```

**驗證**：
- 句型種類 >= 5
- 隨機選擇覆蓋

#### Step 7: 整合後處理模組
將三個庫整合到 `src/functions/utils/post_processing.py`

**驗證**：
- 整合測試通過
- 不影響現有功能
- 回歸測試通過

---

## 測試執行

### 單元測試
```bash
python -m pytest tests/test_structure_library.py -v
```

### 整合測試
```bash
python scripts/test_structure_diversification.py
```

### 回歸測試
```bash
python scripts/test_svc_errors.py
python scripts/test_markdown_cleanup.py
```

---

## 每步完成後的動作

1. 執行測試驗證
2. 更新 `DEVELOPMENT_LOG.md` 記錄完成
3. 確認沒有破壞現有功能
4. 準備下一步

---

## 禁止事項

- ❌ 不修改 ErrorCode
- ❌ 不改變 API 回應格式（LLMOutput schema）
- ❌ 不修改現有後處理邏輯（Markdown 清理等）
- ❌ 不修改 template_differentiator
- ❌ 不修改 word_count_validator

---

## 成功標準

| 指標 | 目標 |
|------|------|
| 固定格式開頭率 | < 20% |
| 開頭句型種類 | >= 3 種 |
| 文章框架種類 | >= 6 |
| 情境開頭種類 | >= 5 |
| 句型種類 | >= 5 |
| 回歸測試 | 全部通過 |