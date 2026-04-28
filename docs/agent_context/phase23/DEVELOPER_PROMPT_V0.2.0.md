# Phase 23 重新開發 Developer Prompt

## 問題陳述

Phase 23 目前只做到「選擇模板」+「記錄日誌」，**沒有把模板應用到輸出內容**。

這導致：
- API 生成的內容沒有變化
- 問題解決不了

---

## 完成標準

### ✅ 完成條件（全部滿足）

| # | 條件 | 驗證方式 |
|---|------|----------|
| 2.1 | 調用 API 生成 3 次**同一間公司**，開頭不完全相同 | 實際調用 API |
| 2.2 | 段落順序不永遠相同 | 檢查輸出 |
| 2.3 | 句型有變化 | 檢查句子結構 |

### ❌ 失敗條件

| # | 條件 |
|---|------|
| F1 | 連續 3 次輸出，開頭完全相同 |
| F2 | 段落順序完全一樣 |

---

## 實現方案：Prompt 傳遞方式（推薦）

### 核心概念

不是「後處理時硬改內容」，而是」生成時就把模板傳給 LLM，讓它參考」。

### 實現步驟

#### Step 1: 修改 Prompt 模板

在 `generate_prompt_template.txt` 中加入占位符：

```
## 框架指導
框架類型: {structure_type}
段落順序: {structure_flow}
情境開頭示例: {opening_example}
句型參考: {sentence_example}

## 撰寫原則
1. 語氣專業且親切
2. 突出公司核心競爭力
3. 避免誇大不實的描述
4. 使用繁體中文
5. 參考上述框架指導進行撰寫
6. 開頭多樣化（參考情境開頭示例）
7. 段落結構多樣化（參考框架類型）
8. 句型變化（參考句型參考）
```

#### Step 2: 修改 prompt_builder.py

```python
def build_generate_prompt(
    company_data: dict,
    structure_key: str = None,
    opening_key: str = None,
    sentence_key: str = None
) -> str:
    """構建生成 Prompt"""
    
    # 1. 選擇框架
    if structure_key is None:
        structure_key = get_random_structure()
    
    # 2. 選擇情境
    if opening_key is None:
        opening_key = get_random_opening()
    
    # 3. 選擇句型
    if sentence_key is None:
        sentence_key = get_random_sentence_pattern()
    
    # 4. 渲染框架資訊
    structure_guide = f"""框架類型: {structure_key}
段落順序: {' → '.join(get_structure_flow(structure_key))}
"""
    
    # 5. 渲染情境開頭
    opening_example = render_opening(opening_key, **company_data)
    opening_guide = f"""情境開頭示例: {opening_example}
"""
    
    # 6. 渲染句型參考
    sentence_example = render_sentence(sentence_key, **company_data)
    sentence_guide = f"""句型參考: {sentence_example}
"""
    
    # 7. 組合
    template_guide = structure_guide + opening_guide + sentence_guide
    
    # 8. 讀取原始 Prompt 並替換
    prompt = read_prompt_template("generate")
    prompt = prompt.replace("{structure_type}", structure_key)
    prompt = prompt.replace("{structure_flow}", " → ".join(get_structure_flow(structure_key)))
    prompt = prompt.replace("{opening_example}", opening_example)
    prompt = prompt.replace("{sentence_example}", sentence_example)
    
    return prompt
```

#### Step 3: 修改 generate_node.py

```python
def generate_node(state):
    """生成節點"""
    company_data = get_company_data(state)
    
    # 每次生成都隨機選擇模板
    structure_key = get_random_structure()
    opening_key = get_random_opening()
    sentence_key = get_random_sentence_pattern()
    
    # 記錄日誌（便於 Debug）
    logger.info(f"[Phase23] 選擇框架: {structure_key}")
    logger.info(f"[Phase23] 選擇情境: {opening_key}")
    logger.info(f"[Phase23] 選擇句型: {sentence_key}")
    
    # ���給 prompt_builder
    prompt = build_generate_prompt(
        company_data,
        structure_key=structure_key,
        opening_key=opening_key,
        sentence_key=sentence_key
    )
    
    # 調用 LLM
    response = llm.invoke(prompt)
    
    return {"content": response}
```

---

## 需要修改的檔案

| 檔案 | 更改 |
|------|------|
| `src/functions/generate_prompt_template.txt` | 加入占位符 |
| `src/functions/utils/prompt_builder.py` | 新增 build_generate_prompt() 函式 |
| `src/langgraph_state/company_brief_graph.py` 或 `src/functions/generate_brief.py` | 調用時傳遞模板參數 |

---

## 驗證方式

```bash
# 測試多次同一間公司
curl -X POST .../process -d '{"organ": "台積電", ...}'
curl -X POST .../process -d '{"organ": "台積電", ...}'
curl -X POST .../process -d '{"organ": "台積電", ...}'

# 檢查輸出
# 如果開頭不同，則成功
# 如果段落順序不同，則成功
```

---

## 決不修改

| 檔案 | 原因 |
|------|------|
| ErrorCode | 維持錯誤處理標準化 |
| API 回應格式 | 維持向后相容 |
| markdown_cleaner | 維持 Phase 22 功能 |
| word_count_validator | 維持字數限制 |

---

## 提交前檢查清單

- [ ] Prompt 有占位符
- [ ] prompt_builder.py 有 build_generate_prompt()
- [ ] generate_node 調用時有傳遞模板參數
- [ ] 日誌有記錄選擇的模板
- [ ] 實際 API 調用測試通過（開頭不同）