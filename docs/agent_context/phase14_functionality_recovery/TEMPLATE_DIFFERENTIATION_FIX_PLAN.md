# Phase 14 Stage 2 - 模板差異化修復工作規劃

## 日期：2026-04-10

## 1. 問題背景

### 1.1 發現的問題

經過整合測試發現，模板差異化功能存在根本性架構問題：

| 症狀 | 說明 |
|------|------|
| 三個模板輸出相同 | Brief/Standard/Detailed 都是 73 字 |
| 風格無差異 | LLM 生成時不知道用戶選擇了哪個模板 |
| 後處理無效 | `differentiate_template()` 只能截斷，不能改變風格 |

### 1.2 根本原因

```
┌─────────────────────────────────────────────────────────────┐
│                    問題根因                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  optimization_mode 參數在新流程中沒有傳遞                     │
│           ↓                                                  │
│  prompt_builder.py 不知道用戶選擇了哪個模板                   │
│           ↓                                                  │
│  LLM 生成相同內容                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 架構對比

| 組件 | 舊流程 | 新流程 |
|------|--------|--------|
| API 參數 | `optimization_mode` ✅ | ❌ 沒有傳遞 |
| LLM Service | BedrockLLMService | LangGraph |
| Prompt 區分 | 有 mode_descriptions | ❌ 沒有 |
| 結果 | LLM 知道模板 | ❌ 不知道 |

---

## 2. 解決方案

### 2.1 完整解決方案（兩個部分缺一不可）

| 步驟 | 內容 | 缺少會怎樣 |
|------|------|-----------|
| **第一步** | 修復參數傳遞 | ❌ `prompt_builder` 不知道用哪個模板 |
| **第二步** | Prompt 層區分 | ❌ 沒有參數，無法區分 |

### 2.2 目標流程

```
用戶選擇 "CONCISE" (簡潔模式)
           ↓
API 請求包含 optimization_mode=2
           ↓
generate_brief(..., optimization_mode=2)
           ↓
generate_company_brief(..., optimization_mode=2)
           ↓
prompt_builder(..., template_type="concise")
           ↓
if template_type == "concise":
    prompt += "請生成一段極簡的公司簡介，重點是公司名稱和核心業務。"
elif template_type == "detailed":
    prompt += "請生成一段詳細的公司簡介，包含成立背景、服務項目、團隊規模、未來願景等。"
           ↓
LLM 生成符合模板要求的內容
           ↓
differentiate_template() 只做精確截斷
           ↓
三個模板輸出明顯不同 ✅
```

---

## 3. 工作項目詳細規劃

### 3.1 第一步：修復參數傳遞

#### 工項 1.1：修改 `generate_brief.py`

**檔案**: `src/functions/utils/generate_brief.py`

**修改內容**:
```python
def generate_brief(data):
    # ... 現有代碼 ...
    optimization_mode = data.get("optimization_mode")  # 新增

    result = generate_company_brief(
        organ=organ,
        organ_no=organ_no,
        company_url=company_url,
        user_brief=user_brief,
        word_limit=word_limit,
        capital=capital,
        employees=employees,
        founded_year=founded_year,
        optimization_mode=optimization_mode,  # 新增這一行
    )
```

**測試**:
- [ ] 呼叫 `generate_brief` 時傳遞 `optimization_mode`
- [ ] 確認參數傳遞到 `generate_company_brief`

#### 工項 1.2：修改 `company_brief_graph.py`

**檔案**: `src/langgraph/company_brief_graph.py`

**修改內容**:
1. 在 `generate_company_brief()` 函數添加 `optimization_mode` 參數
2. 在狀態定義中添加 `optimization_mode`
3. 在 LLM 節點中傳遞 `optimization_mode` 到 prompt
4. 在 `build_generate_prompt` 呼叫中添加 `optimization_mode`

**代碼範例**:
```python
def generate_company_brief(
    organ,
    organ_no=None,
    company_url=None,
    user_brief=None,
    word_limit=None,
    capital=None,
    employees=None,
    founded_year=None,
    optimization_mode=None,  # 新增
):
    # ... 構建狀態 ...
    initial_state = {
        "organ": organ,
        "organ_no": organ_no,
        # ...
        "optimization_mode": optimization_mode,  # 新增
    }
```

**測試**:
- [ ] 確認 `optimization_mode` 傳遞到 LangGraph 狀態
- [ ] 確認 `optimization_mode` 傳遞到 LLM 節點

---

### 3.2 第二步：Prompt 層區分

#### 工項 2.1：修改 `prompt_builder.py`

**檔案**: `src/functions/utils/prompt_builder.py`

**修改內容**:

1. 添加 `template_type` 參數
2. 添加三個模板的描述
3. 在輸出要求中區分模板

**代碼範例**:
```python
# 模板類型描述
TEMPLATE_DESCRIPTIONS = {
    "concise": {
        "name": "簡潔模式",
        "description": "極簡",
        "length_guide": "50-80字",
        "content_guide": "請生成一段極簡的公司簡介，重點是公司名稱和核心業務。保留最重要的信息，去除所有修飾性描述。",
    },
    "standard": {
        "name": "標準模式",
        "description": "平衡",
        "length_guide": "150-200字",
        "content_guide": "請生成一段平衡的公司簡介，包含公司背景、核心服務和特色。內容要專業但不死板。",
    },
    "detailed": {
        "name": "詳細模式",
        "description": "詳細",
        "length_guide": "300-500字",
        "content_guide": "請生成一段詳細的公司簡介，包含成立背景、服務項目、團隊規模、技術實力、發展歷程、未來願景等。內容要豐富完整。",
    },
}

def build_generate_prompt(
    organ,
    organ_no=None,
    # ... 其他現有參數 ...
    optimization_mode=None,  # 新增
):
    # ... 現有代碼 ...
    
    # 新增：根據模板類型添加描述
    if optimization_mode:
        template_info = TEMPLATE_DESCRIPTIONS.get(optimization_mode, TEMPLATE_DESCRIPTIONS["standard"])
        sections.append(f"\n## 輸出模式")
        sections.append(f"模式：{template_info['name']}")
        sections.append(f"長度：{template_info['length_guide']}")
        sections.append(f"要求：{template_info['content_guide']}")
    
    # ... 現有代碼 ...
```

**測試**:
- [ ] 測試 Brief 模板生成的內容簡潔
- [ ] 測試 Standard 模板生成的內容平衡
- [ ] 測試 Detailed 模板生成的內容詳細

---

### 3.3 第三步：簡化後處理

#### 工項 3.1：修改 `differentiate_template()`

**檔案**: `src/functions/utils/template_differentiator.py`

**修改原則**:
- 移除風格相關的處理邏輯
- 只保留精確截斷功能
- 添加日誌說明這只是截斷，不是風格控制

**測試**:
- [ ] Brief 模板截斷到 100 字
- [ ] Standard 模板截斷到 200 字
- [ ] Detailed 模板截斷到 500 字

---

### 3.4 第四步：整合測試

#### 工項 4.1：撰寫整合測試

**檔案**: `tests/test_template_integration.py`

**測試內容**:
```python
def test_three_templates_different():
    """測試三個模板生成不同的內容"""
    
    # 準備測試資料
    test_input = {...}
    
    # 測試三個模板
    brief_result = generate_brief({**test_input, "optimization_mode": "concise"})
    standard_result = generate_brief({**test_input, "optimization_mode": "standard"})
    detailed_result = generate_brief({**test_input, "optimization_mode": "detailed"})
    
    # 驗證差異
    assert len(brief_result) < len(standard_result)
    assert len(standard_result) < len(detailed_result)
    
    # 驗證內容差異
    brief_text = strip_html(brief_result)
    detailed_text = strip_html(detailed_result)
    similarity = calculate_similarity(brief_text, detailed_text)
    assert similarity < 0.7  # 相似度低於 70%
```

**測試項目**:
- [ ] 三個模板長度遞增
- [ ] 三個模板內容有差異
- [ ] Brief 簡潔明了
- [ ] Standard 平衡專業
- [ ] Detailed 詳細完整

---

## 4. 預計時間

| 工項 | 內容 | 預計時間 |
|------|------|---------|
| 1.1 | 修改 generate_brief.py | 0.5 小時 |
| 1.2 | 修改 company_brief_graph.py | 2 小時 |
| 2.1 | 修改 prompt_builder.py | 3 小時 |
| 3.1 | 簡化 differentiate_template() | 1 小時 |
| 4.1 | 撰寫整合測試 | 2 小時 |
| 4.2 | 執行測試並修復問題 | 2 小時 |
| **總計** | | **10.5 小時** |

---

## 5. 交付物

| 交付物 | 檔案位置 |
|--------|---------|
| 修改後的 generate_brief.py | `src/functions/utils/generate_brief.py` |
| 修改後的 company_brief_graph.py | `src/langgraph/company_brief_graph.py` |
| 修改後的 prompt_builder.py | `src/functions/utils/prompt_builder.py` |
| 修改後的 template_differentiator.py | `src/functions/utils/template_differentiator.py` |
| 整合測試 | `tests/test_template_integration.py` |
| 測試報告 | `docs/test_report/v0.0.1/stage2/template_integration_test_report.md` |

---

## 6. 風險與對策

| 風險 | 可能性 | 影響 | 對策 |
|------|--------|------|------|
| LLM 生成內容不符合預期 | 中 | 高 | 調整 Prompt 描述 |
| 參數傳遞有遺漏 | 中 | 高 | 全面測試每個環節 |
| 測試環境與生產環境差異 | 低 | 中 | 使用真實 API 測試 |
| 工作時間超出預期 | 中 | 中 | 預留緩衝時間 |

---

## 7. 成功標準

| 標準 | 目標 | 驗證方法 |
|------|------|---------|
| Brief 模板長度 | 50-100 字 | 測試驗證 |
| Standard 模板長度 | 150-250 字 | 測試驗證 |
| Detailed 模板長度 | 300-500 字 | 測試驗證 |
| 三模板內容差異度 | > 30% | 相似度計算 |
| 功能測試通過率 | 100% | pytest |

---

## 8. 後續行動

1. ✅ 討論並確認方案
2. ⏳ 啟動 Developer Agent
3. ⏳ 執行工項 1.1 - 1.2
4. ⏳ 執行工項 2.1
5. ⏳ 執行工項 3.1
6. ⏳ 執行工項 4.1 - 4.2
7. ⏳ 撰寫階段小結
8. ⏳ 更新 Phase 14 Context

---

## 附錄：相關檔案

| 檔案 | 說明 |
|------|------|
| `src/functions/utils/generate_brief.py` | 主要生成函數 |
| `src/langgraph/company_brief_graph.py` | LangGraph 流程 |
| `src/functions/utils/prompt_builder.py` | Prompt 建構 |
| `src/functions/utils/template_differentiator.py` | 模板差異化 |
| `docs/agent_context/phase14_functionality_recovery/` | Phase 14 Context |
| `docs/test_report/v0.0.1/stage2/agent_fg_stage2_assessment_report.md` | 評估報告 |
