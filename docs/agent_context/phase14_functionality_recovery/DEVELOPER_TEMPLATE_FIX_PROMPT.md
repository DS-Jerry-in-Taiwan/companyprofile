# Developer Agent Prompt - Phase 14 Stage 2 模板差異化修復

## 任務概述

你是 Developer Agent，負責實作 Phase 14 Stage 2 的模板差異化修復工作。

**問題背景**：
經過整合測試發現，三個模板（concise/standard/detailed）輸出完全相同。這是因為 `optimization_mode` 參數在新流程中沒有傳遞，導致 LLM 生成時不知道用戶選擇了哪個模板。

**目標**：
讓三個模板生成明顯不同的內容：
- Brief (concise): 50-100 字，極簡
- Standard: 150-250 字，平衡
- Detailed: 300-500 字，詳細

---

## 參考文件

請先閱讀以下文件：

1. **工作規劃文件**：`docs/agent_context/phase14_functionality_recovery/TEMPLATE_DIFFERENTIATION_FIX_PLAN.md`
2. **評估報告**：`docs/test_report/v0.0.1/stage2/agent_fg_stage2_assessment_report.md`
3. **進度追蹤**：`docs/agent_context/phase14_functionality_recovery/PROGRESS_TRACKING.md`

---

## 工作步驟

### 第一步：修復參數傳遞

#### 工項 1.1：修改 `src/functions/utils/generate_brief.py`

1. 在 `generate_brief()` 函數中接收 `optimization_mode` 參數
2. 將 `optimization_mode` 傳遞到 `generate_company_brief()` 函數

**代碼範例**：
```python
def generate_brief(data):
    # ... 現有代碼 ...
    optimization_mode = data.get("optimization_mode")  # 新增

    result = generate_company_brief(
        # ... 現有參數 ...
        optimization_mode=optimization_mode,  # 新增這一行
    )
```

#### 工項 1.2：修改 `src/langgraph/company_brief_graph.py`

1. 在 `generate_company_brief()` 函數添加 `optimization_mode` 參數
2. 在狀態定義中添加 `optimization_mode`
3. 在 LLM 節點中傳遞 `optimization_mode` 到 prompt

**代碼範例**：
```python
def generate_company_brief(
    organ,
    organ_no=None,
    # ... 其他參數 ...
    optimization_mode=None,  # 新增
):
    # 構建狀態
    initial_state = {
        "organ": organ,
        # ... 其他狀態 ...
        "optimization_mode": optimization_mode,  # 新增
    }
```

---

### 第二步：Prompt 層區分

#### 工項 2.1：修改 `src/functions/utils/prompt_builder.py`

1. 添加 `TEMPLATE_DESCRIPTIONS` 字典，定義三個模板的描述
2. 在 `build_generate_prompt()` 函數添加 `optimization_mode` 參數
3. 根據模板類型添加不同的輸出要求

**代碼範例**：
```python
# 模板類型描述
TEMPLATE_DESCRIPTIONS = {
    "concise": {
        "name": "簡潔模式",
        "length_guide": "50-80字",
        "content_guide": "請生成一段極簡的公司簡介，重點是公司名稱和核心業務。",
    },
    "standard": {
        "name": "標準模式",
        "length_guide": "150-200字",
        "content_guide": "請生成一段平衡的公司簡介，包含公司背景和核心服務。",
    },
    "detailed": {
        "name": "詳細模式",
        "length_guide": "300-500字",
        "content_guide": "請生成一段詳細的公司簡介，包含成立背景、服務項目、團隊規模、未來願景等。",
    },
}

def build_generate_prompt(
    organ,
    # ... 其他參數 ...
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
```

---

### 第三步：簡化後處理

#### 工項 3.1：修改 `src/functions/utils/template_differentiator.py`

1. 移除風格相關的處理邏輯
2. 只保留精確截斷功能
3. 添加日誌說明這只是截斷，不是風格控制

---

### 第四步：整合測試

#### 工項 4.1：撰寫整合測試 `tests/test_template_integration.py`

```python
def test_three_templates_different():
    """測試三個模板生成不同的內容"""
    
    test_input = {
        "organ": "測試公司",
        "brief": "這是一家專業的科技公司...",
    }
    
    # 測試三個模板
    brief_result = generate_brief({**test_input, "optimization_mode": "concise"})
    standard_result = generate_brief({**test_input, "optimization_mode": "standard"})
    detailed_result = generate_brief({**test_input, "optimization_mode": "detailed"})
    
    # 驗證長度差異
    assert len(brief_result["body_html"]) < len(standard_result["body_html"])
    assert len(standard_result["body_html"]) < len(detailed_result["body_html"])
```

#### 工項 4.2：執行測試並修復問題

1. 執行所有相關測試
2. 如果有失敗，分析原因並修復
3. 確保所有測試通過

---

## 交付物

完成後請交付：

1. **修改後的檔案**：
   - `src/functions/utils/generate_brief.py`
   - `src/langgraph/company_brief_graph.py`
   - `src/functions/utils/prompt_builder.py`
   - `src/functions/utils/template_differentiator.py`

2. **新增的測試檔案**：
   - `tests/test_template_integration.py`

3. **測試結果截圖或日誌**

4. **階段小結**：更新到 `docs/agent_context/phase14_functionality_recovery/PROGRESS_TRACKING.md`

---

## 成功標準

| 標準 | 目標 |
|------|------|
| Brief 模板長度 | 50-100 字 |
| Standard 模板長度 | 150-250 字 |
| Detailed 模板長度 | 300-500 字 |
| 三模板內容差異度 | > 30% |
| 功能測試通過率 | 100% |

---

## 注意事項

1. **不要破壞現有功能**：確保修改不會影響其他功能
2. **保持向後相容**：沒有傳遞 `optimization_mode` 時，預設為 `standard`
3. **添加日誌**：方便日後追蹤問題
4. **撰寫測試**：確保功能被測試覆蓋

---

## 開始工作

請按照上述步驟執行，並在完成後：
1. 執行測試驗證
2. 撰寫階段小結
3. 更新到 Phase 14 Context

祝順利！
