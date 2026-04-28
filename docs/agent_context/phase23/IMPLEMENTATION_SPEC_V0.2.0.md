# Phase 23 完整實現規格書 v0.2.0

## 版本
- **文件版本**: v0.2.0
- **建立日期**: 2026-04-24
- **狀態**: 重新定義

---

## 1. 問題陳述

### v0.2.0 測試報告問題

| # | 問題 | 優先級 | 目前狀態 |
|---|------|------|----------|
| #2 | 模板過於一致 | 一般 | ⚠️ 未真正解決 |
| #3 | 句型僵化 | 一般 | ⚠️ 未真正解決 |

### 問題具體表現

- 每篇公司簡介都以「[公司]成立於[年份]年」開頭
- 段落順序永遠是「成立→理念→服務→競爭力→未來」
- 通篇使用相同句型結構

---

## 2. 完成標準（什麼叫「完成」）

### ✅ 完成條件（全部滿足）

| # | 條件 | 驗證方式 |
|---|------|----------|
| 2.1 | 調用 API 生成 5 次**同一間公司**，開頭不完全相同 | 人工檢查 |
| 2.2 | 段落順序不永遠相同 | 人工檢查輸出的段落排列 |
| 2.3 | 句型有變化 | 人工檢查句子結尾/開頭結構 |

### ❌ 失敗條件（任一滿足即失敗）

| # | 條件 |
|---|------|
| F1 | 連續 3 次輸出，開頭完全相同 |
| F2 | 段落順序完全一樣 |
| F3 | 沒有任何「成立於」的開頭（全部都是）|

---

## 3. 通過標準（怎麼驗證）

### 驗證方式 A：API 實際調用（需要 API 配額）

```bash
# 對同一間公司調用 3 次
curl -X POST http://localhost:5000/v1/company/profile/process \
  -d '{"organ": "台積電", "organNo": "12345678", ...}'
# 重複 3 次，檢查輸出差異
```

**通過標準**：
- 3 次輸出中，至少有 2 次開頭不同
- 或 3 次輸出中，段落順序至少有 1 次不同

### 驗證方式 B：單元測試（不需要 API）

```bash
# 測試框架選擇隨機性
python -m pytest tests/test_structure_library.py::TestRandomSelection::test_framework_randomness

# 測試多次調用差異
python scripts/test_multiple_same_company.py
```

**通過標準**：
- 執行 50 次，至少覆蓋 3 種不同框架
- 執行 30 次，至少覆蓋 2 種不同句型

---

## 4. 實現方案

### 方式 A：Prompt 傳遞（推薦）

**做法**：把選擇的模板傳給 LLM Prompt，讓它生成時參考

**優點**：
- 實現簡單
- LLM 理解能力強
- 不會破壞輸出語意

**缺點**：
- 需要修改 Prompt 模板

**實現位置**：
1. `generate_prompt_template.txt` — 加入框架/情境/句型變數
2. `prompt_builder.py` — 傳遞選擇的模板到 Prompt

### 方式 B：後處理套用

**做法**：生成後，根據選擇的模板重新組裝內容

**優點**：
- 完全控制輸出

**缺點**：
- 實現複雜
- 可能破壞語意

---

## 5. 實現細節（方式 A）

### Step 1: 修改 Prompt 模板

```python
# generate_prompt_template.txt 新增

## 框架指導（會傳入）
框架類型: {structure_type}
情境開頭: {situation_opening}
句型風格: {sentence_pattern}

## 撰寫原則
1. 語氣專業且親切
2. 突出公司核心競爭力
3. 避免誇大不實的描述
4. 使用繁體中文
5. 參考上述框架指導進行撰寫
```

### Step 2: 修改 prompt_builder.py

```python
def build_prompt(..., structure_key=None, opening_key=None, sentence_key=None):
    # 渲染框架資訊
    structure_guide = ""
    if structure_key:
        flow = get_structure_flow(structure_key)
        structure_guide = f"框架類型: {structure_key}\\n段落順序: {' → '.join(flow)}\\n"
    
    # 渲染情境
    opening_guide = ""
    if opening_key:
        rendered = render_opening(opening_key, **company_data)
        opening_guide = f"情境開頭: {rendered}\\n"
    
    # 渲染句型
    sentence_guide = ""
    if sentence_key:
        template = SENTENCE_PATTERNS[sentence_key]
        sentence_guide = f"句型風格: {template}\\n"
    
    # 組合
    full_guide = structure_guide + opening_guide + sentence_guide
    return prompt.replace("{template_guide}", full_guide)
```

### Step 3: 修改 generate_node.py

```python
# 在調用 LLM 之前，先選取模板
structure_key = get_random_structure()
opening_key = get_random_opening()
sentence_key = get_random_sentence_pattern()

# 傳給 prompt_builder
prompt = build_prompt(
    ...,
    structure_key=structure_key,
    opening_key=opening_key,
    sentence_key=sentence_key
)
```

---

## 6. 失敗回退

如果方式 A 效果不好：

| 策略 | 說明 |
|------|------|
| 回退到方式 B | 改用後處理套用 |
| 混合方式 | Prompt + 後處理雙重保障 |
| 放棄 | 如果代價太高，考慮放棄此功能 |

---

## 7. 版本控制

| 版本 | 日期 | 變更 |
|------|------|------|
| v0.1.0 | 2026-04-23 | 初始版本（選擇功能，未應用）|
| v0.2.0 | 2026-04-24 | 重新定義完成標準，改為 Prompt 傳遞方式 |

---

## 8. 審查清單（更新版）

在提交 PR 前，確認以下項目：

- [ ] 完成標準已定義（v0.2.0）
- [ ] 通過標準已定義（可實際驗證）
- [ ] Prompt 已加入框架傳遞變數
- [ ] prompt_builder.py 已更新
- [ ] generate_node.py 已傳遞模板參數
- [ ] API 實際調用測試通過（方式 A）
- [ ] 或單元測試通過（方式 B）
- [ ] 沒有修改禁止的檔案
- [ ] 版本更新

---

## 9. 驗證記錄

### 驗證記錄表

| 日期 | 驗證方式 | 結果 | 記錄人 |
|------|----------|------|--------|
|      |          |      |        |