# Phase 22: Markdown 格式清理優化

## 版本
- **文件版本**: v0.2.0
- **建立日期**: 2026-04-23
- **完成日期**: 2026-04-23
- **前置版本**: Phase 21 (v0.3.6)
- **目標版本**: v0.3.7

---

## 目標

移除 LLM 生成公司簡介時夾帶的 Markdown 格式語法（`**`、`##`、`###` 等），確保輸出為純文字或標準 HTML。

### 問題背景

根據 `docs/test_report/v0.2.0/1111 公司簡介生成優化-sug.xlsx`：

> **格式汙染**：實際產出有 markdown 格式，例如 `**艾兒莫拉韓系服飾**秉持著專業與穩健的經營精神`

### 根本原因

| 環節 | 問題 |
|------|------|
| Prompt 層 | Few-shot 範例未明確禁止 Markdown 輸出 |
| 解析層 | `LLMOutput` 解析後未清理 Markdown |
| 後處理層 | `post_processing.py` 只有 HTML 處理，無 Markdown 清理 |

---

## 預期成果

| 指標 | 目標 |
|------|------|
| Markdown 殘留率 | 0% |
| 處理速度 | < 50ms |
| 誤傷率 | < 1%（不影響正常星號內容）|

---

## 相關檔案

### 需要修改
- `src/services/llm_service.py` - LLM 輸出解析
- `src/functions/utils/post_processing.py` - 後處理清理

### 新增檔案
- `src/functions/utils/markdown_cleaner.py` - Markdown 清理模組
- `tests/test_markdown_cleaner.py` - 單元測試

### 測試檔案
- `scripts/test_markdown_cleanup.py` - 整合測試腳本

---

## 開發順序

1. **Step 1**: 建立 `markdown_cleaner.py` 單元測試（TDD）
2. **Step 2**: 實作 `markdown_cleaner.py` 清理邏輯
3. **Step 3**: 在 `llm_service.py` 或 `post_processing.py` 整合清理
4. **Step 4**: 整合測試驗證
5. **Step 5**: 更新 Prompt 範例（可選）

---

## 禁止事項

1. ❌ 不修改 `try-catch` 邏輯
2. ❌ 不改變 LLM API 呼叫參數
3. ❌ 不修改 `ErrorCode` 枚舉
4. ❌ 不改變現有的 `LLMOutput` schema
5. ❌ 不在 Prompt 中直接禁止 Markdown（由後處理處理）

---

## 驗證標準

### 單元測試（test_markdown_cleaner.py）
- [x] `**bold**` → `bold`
- [x] `## Header` → `Header`
- [x] `### Header` → `Header`
- [x] 電話格式保護 `***-****-****`
- [x] 性能 < 50ms

### 整合測試（test_markdown_cleanup.py）
- [x] 真實 LLM 輸出無 Markdown
- [x] 處理速度 < 50ms
- [x] 不影響正常星號（如電話號碼 `***-****-****`）

---

## 下一步

→ 閱讀 `DEVELOPMENT_PLAN_DETAIL.md` 開始開發