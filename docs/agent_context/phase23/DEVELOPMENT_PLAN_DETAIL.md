# Phase 23 詳細實作計劃

## 版本
- **文件版本**: v0.1.0
- **建立日期**: 2026-04-23
- **目標版本**: v0.3.8

---

## 實作階段概覽

| 階段 | 工項 | 預估時間 |
|------|------|----------|
| Phase 23a | Prompt 更新 | 1 小時 |
| Phase 23b | 模板庫實作 | 2 小時 |

---

## Phase 23a: Prompt 更新

### Step 1: 修改 generate_prompt_template.txt

**目標**：在 Prompt 中加入多樣化撰寫原則

**修改內容**：

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
   - 可以使用陳述句、問句、感嘆句等不同語氣
```

**測試目標**：
- [ ] Prompt 修改完成
- [ ] Few-shot 範例更新（3+ 種不同開頭）

**指標**：
- Prompt 字數增加合理（不超過 500 字）
- Few-shot 涵蓋不同開頭類型

---

### Step 2: 修改 optimize_prompt_template.txt

**目標**：同步修改優化 Prompt

**修改內容**：

```
## 優化指令
1. 保留原始簡介中的核心事實
2. 補充缺失的重要資訊
3. 改善語句流暢度與專業度
4. 確保內容真實且不誇大
5. 開頭多樣化
   - 不要使用「[公司]成立於[年份]年」的固定格式
   - 優先以「核心服務/產品特色」開頭
6. 段落結構多樣化
   - 不一定要按固定順序
```

**測試目標**：
- [ ] Prompt 修改完成
- [ ] 與 generate_prompt_template.txt 一致

**指標**：
- 兩份 Prompt 結構一致

---

### Step 3: 整合測試

**目標**：驗證 Prompt 更新後的輸出多樣性

**測試案例**：

| 編號 | 輸入 | 預期 |
|------|------|------|
| T1 | 標準產業 | 開頭不使用固定格式 |
| T2 | 科技產業 | 可使用情境開頭 |
| T3 | 服務業 | 可使用服務優先結構 |
| T4 | 多次執行同一家公司 | 開頭有變化 |

**指標**：
- 固定格式開頭率 < 20%
- 開頭句型種類 >= 3 種

---

## Phase 23b: 模板庫實作

### Step 4: 建立文章框架庫

**目標**：提供 6 種段落順序

**實作內容**：

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

**測試目標**：
- [ ] 6 種框架定義完成
- [ ] 隨機選擇邏輯實作
- [ ] 單元測試通過

**指標**：
- 框架種類 >= 6
- 隨機選擇覆蓋所有框架

---

### Step 5: 建立情境庫

**目標**：提供 5 種情境開頭

**實作內容**：

```python
SITUATION_OPENINGS = {
    "industry": "在{industry}領域，{company}...",
    "market": "面對{trend}，{company}...",
    "problem": "針對{challenge}，{company}...",
    "trend": "隨著{trend}，{company}...",
    "user": "當你需要{service}，{company}...",
}
```

**測試目標**：
- [ ] 5 種情境定義完成
- [ ] 情境變數替換邏輯
- [ ] 單元測試通過

**指標**：
- 情境種類 >= 5
- 變數替換正確率 100%

---

### Step 6: 建立句型庫

**目標**：提供 5+ 種句型

**實作內容**：

```python
SENTENCE_PATTERNS = {
    "service": "專注於{industry}的{company}，提供{service}。",
    "feature": "以{feature}聞名的{company}，{action}。",
    "data": "擁有{years}年歷史的{company}，{description}。",
    "question": "想找{service}嗎？{company}是您的最佳選擇。",
    "situation": "{situation}，{company}{action}。",
}
```

**測試目標**：
- [ ] 5+ 種句型定義完成
- [ ] 句型選擇邏輯
- [ ] 單元測試通過

**指標**：
- 句型種類 >= 5
- 隨機選擇覆蓋所有句型

---

### Step 7: 整合後處理模組

**目標**：將三個庫整合到 post_processing.py

**實作內容**：

```python
def diversify_content(
    text: str,
    industry: str = None,
    company: str = None,
    service: str = None,
    foundation_year: str = None,
    feature: str = None
) -> str:
    # 1. 選擇文章框架
    # 2. 套用情境開頭
    # 3. 替換句型
    return diversified_text
```

**測試目標**：
- [ ] 整合到 post_processing.py
- [ ] 整合測試通過

**指標**：
- 整合測試通過率 100%
- 不影響現有功能

---

## 測試矩陣

### 單元測試

| 測試項 | 測試內容 | 通過標準 |
|--------|----------|----------|
| UT-01 | 文章框架庫 - 隨機選擇 | 覆蓋 6 種框架 |
| UT-02 | 情境庫 - 變數替換 | 正確替換所有變數 |
| UT-03 | 句型庫 - 隨機選擇 | 覆蓋 5 種句型 |
| UT-04 | 整合測試 - 輸出多樣 | 固定開頭率 < 20% |

### 整合測試

| 測試項 | 測試內容 | 通過標準 |
|--------|----------|----------|
| IT-01 | Prompt 生成測試 | 開頭不使用固定格式 |
| IT-02 | 後處理測試 | 框架隨機變化 |
| IT-03 | 多次執行測試 | 開頭有變化 |
| IT-04 | 回歸測試 | 不影響現有功能 |

---

## 下一步

1. ✅ 建立 `DEVELOPMENT_PLAN_DETAIL.md`
2. → 建立 `TEST_METRICS.md`
3. → 建立 `TASK_BOUNDARIES.md`
4. → 開始 Phase 23a 實作