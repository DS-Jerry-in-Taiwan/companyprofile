# Phase 18：Developer Agent 開發指令

**日期**: 2026-04-17
**目標**: 實作 Structured Output 優化 ParallelAspectSearchTool

---

## 🎯 任務概述

將 `ParallelAspectSearchTool` 改用 **Gemini Structured Output**，確保輸出格式一致，解決 foundation 回傳 dict 而非字串的問題。

---

## 📋 開發步驟

### 步驟 1：問題分析

1. 執行測試腳本確認問題
2. 分析 Prompt 和解析邏輯
3. 選擇解決方案（Structured Output）

**參考文件**：`01_issue_analysis.md`

---

### 步驟 2：Schema 設計

1. 定義四面向的輸出 Schema
2. 設計 `GenerateContentConfig`
3. 簡化 Prompt

**參考文件**：`02_solution_design.md`

---

### 步驟 3：程式實作

1. 修改 `src/services/search_tools.py` 中的 `ParallelAspectSearchTool`
2. 加入 `response_schema` 和 `response_mime_type`
3. 更新 `_search_single_aspect` 方法

**參考文件**：`03_implementation.md`

---

### 步驟 4：整合測試

1. 單元測試：驗證輸出格式
2. 整合測試：通過 `summary_node`
3. Checkpoint 1 測試

**參考文件**：`04_test_plan.md`

---

### 步驟 5：文件更新

1. 更新 README
2. 產出測試報告
3. 提交程式碼

**參考文件**：`05_acceptance_criteria.md`

---

## 🚀 快速開始

```bash
cd /home/ubuntu/projects/OrganBriefOptimization

# 1. 確認問題
python3 -c "
from src.services.search_tools import ParallelAspectSearchTool
tool = ParallelAspectSearchTool(timeout=30)
result = tool.search('澳霸有限公司')
for k, v in result.data.items():
    print(f'{k}: {type(v).__name__}')
"

# 2. 實作修改
# 編輯 src/services/search_tools.py

# 3. 執行測試
python3 -c "
from src.services.search_tools import ParallelAspectSearchTool
tool = ParallelAspectSearchTool(timeout=30)
result = tool.search('台積電')
for k, v in result.data.items():
    assert isinstance(v, str), f'{k} should be str'
print('✅ 測試通過')
"

# 4. Checkpoint 1 測試
python3 scripts/checkpoint1/test_phase17_complete_flow.py
```

---

## 📁 開發文件索引

| 文件 | 說明 |
|------|------|
| [README.md](./README.md) | 總覽 |
| [phase18-development-plan.md](./phase18-development-plan.md) | 開發規劃 |
| [01_issue_analysis.md](./01_issue_analysis.md) | 問題分析 |
| [02_solution_design.md](./02_solution_design.md) | 解決方案設計 |
| [03_implementation.md](./03_implementation.md) | 實作細節 |
| [04_test_plan.md](./04_test_plan.md) | 測試計畫 |
| [05_acceptance_criteria.md](./05_acceptance_criteria.md) | 驗收標準 |

---

## ✅ 完成標準

1. `ParallelAspectSearchTool` 所有面向輸出皆為 `str` 類型
2. `summary_node` 處理不會失敗
3. Checkpoint 1 測試通過
4. 輸出內容豐富度恢復（> 100 字/面向）

---

*最後更新：2026-04-17*
