# Phase 22 Developer Prompt

## 版本
- **文件版本**: v0.2.0
- **建立日期**: 2026-04-23
- **完成日期**: 2026-04-23
- **狀態**: ✅ Phase 22 完成（v0.3.7 已發布）

## 任務
實作 Markdown 格式清理模組，移除 LLM 輸出中的 `**`、`##`、`###` 等語法。

## 依據文件
- 詳細流程: `docs/agent_context/phase22/DEVELOPMENT_PLAN_DETAIL.md`
- 測試標準: `docs/agent_context/phase22/TEST_METRICS.md`
- 邊界限制: `docs/agent_context/phase22/TASK_BOUNDARIES.md`
- 進度追蹤: `docs/agent_context/phase22/DEVELOPMENT_LOG.md`

## 開發步驟

### Step 1: 建立單元測試
建立 `tests/test_markdown_cleaner.py`，測試案例：
- `**bold**` → `bold`
- `## Header` → `Header`
- `### Header` → `Header`
- 保留 `***-****-****` 電話格式

執行：`python -m pytest tests/test_markdown_cleaner.py -v`

### Step 2: 實作清理模組
建立 `src/functions/utils/markdown_cleaner.py`
- `clean_markdown()` - 標準清理
- `clean_markdown_aggressive()` - 激進清理

### Step 3: 整合（選 B）
在 `src/functions/utils/post_processing.py` 新增 `_clean_markdown()` 函數

### Step 4: 整合測試
建立 `scripts/test_markdown_cleanup.py`，驗證：
- 真實案例無 Markdown 殘留
- 處理速度 < 50ms
- 電話格式完整

## 禁止事項
- ❌ 不修改 ErrorCode
- ❌ 不修改 try-catch 邏輯
- ❌ 不改變 LLMOutput schema
- ❌ 不刪除現有測試

## 成功標準
- 單元測試: 10/10 通過
- 整合測試: 7/7 通過
- 迴歸測試: 4/4 通過
- 版本更新至 v0.3.7