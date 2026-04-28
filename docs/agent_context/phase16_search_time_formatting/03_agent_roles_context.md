# Phase 16 - Agent 角色上下文

**最後更新**: 2026-04-15

## 參與角色

### Architect Agent

**職責**: 規劃與設計（已完成）

**任務**:
- 定義搜尋結果結構化格式
- 規劃開發邊界和限制
- 制定成功標準

**交付物**:
- `01_dev_goal_context.md` - 階段概述、工項、邊界
- `design_spec.md` - 搜尋 prompt 結構化格式定義

### Development Agent

**職責**: 實作與開發

**任務**:
1. 實作搜尋 Prompt 優化（工項 2-3）
2. 實作 Summary Node 更新（工項 4）
3. 執行測試驗證（工項 5）

**分階段指示**:
- 階段 1：完成 `design_spec.md`
- 階段 2：更新 `GeminiFewShotSearchTool` 和 `GeminiPlannerTavilyTool`
- 階段 3：更新 `summary_node` 合併邏輯
- 階段 4：執行測試，確認所有驗收標準通過
- 階段 5：更新文件

**每階段驗收**：
- 完成 → 提供驗證結果 → 等待審核通過 → 繼續下一階段

### QA Agent（可選）

**職責**: 測試驗證

**任務**:
- 執行測試用例（`test_search_formatting.py`）
- 端到端流程測試
- 性能基準測試

**驗收標準**:
- 所有搜尋 provider 返回有效格式
- Generate 輸入品質無退化
- Token 增加在預期內

### Project Manager

**職責**: 進度追蹤

**任務**:
- 監控各階段完成進度
- 收集驗證結果
- 做最終驗收確認

---

## 工作流程

```
設計驗證
    ↓ (Architect 完成 design_spec.md)
搜尋 Prompt 優化
    ↓ (Development 完成，QA 驗證)
Summary Node 更新
    ↓ (Development 完成，QA 驗證)
測試驗證
    ↓ (QA 執行全部測試)
文件更新
    ↓ (Development 完成)
Release 審核
    ↓ (Project Manager 確認)
Release
```

---

## 溝通機制

### 階段完成信號

Development Agent 完成每個階段後，應提供：
1. 修改的文件清單
2. 驗證結果（測試通過 ✅ / 失敗 ❌）
3. 遇到的問題（如有）
4. 準備好的下一階段輸入

### 卡住處理

如果遇到技術問題（如 JSON parse 失敗），應該：
1. 嘗試調整 prompt
2. 實作 fallback 邏輯
3. 記錄問題和解決方案
4. 如有無法解決的問題，向 Architect 報告

---

## 約定

1. **不跨越邊界**：
   - Development 不修改 `generate_node` 本身
   - 不涉及前端改動
   - 不新增監控維度

2. **向後相容**：
   - `summary_node` 輸出格式保持不變
   - `generate_node` 無需改 prompt
   - API 層無需改動

3. **品質保證**：
   - 所有修改都有對應測試
   - 無硬編碼值
   - 代碼風格一致
