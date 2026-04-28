# Phase 14 Stage 3 - Task 0: 前端對齊與模板驗證計劃

**制定日期**: 2026-04-13  
**狀態**: 📋 待執行  
**優先級**: 高 (部署前必做)  
**預估工時**: 0.5 天

---

## 🎯 任務目標

1. **前端清理**: 移除 `word_limit` 輸入欄位，避免用戶困惑。
2. **邏輯統一**: 確保前端完全依賴 `optimization_mode` (模板) 來控制字數。
3. **後端驗證**: 確認後端模板定義正確，且舊版 `word_limit` 邏輯不干擾新流程。
4. **整合測試**: 通過端到端測試，確保全流程運作正常。

---

## 📋 開發步驟與驗證清單

### 🟢 第一階段：前端清理 (Frontend Cleanup)

**目標**: 確保前端不再發送 `word_limit` 參數，且 UI 簡潔。

#### Step 1.1: 移除 UI 元件
*   **檔案**: `frontend/src/components/BriefForm.vue`
*   **操作**:
    1.  搜尋 `word_limit` 相關的 `<label>` 和 `<input>` (約在第 347 行)。
    2.  刪除該區塊。
    3.  刪除 `form` 物件中的 `word_limit: ''` 初始化。
*   **驗證**: 重新啟動前端 (`npm run dev`)，確認頁面上已無「字數限制」輸入框。

#### Step 1.2: 清理提交邏輯
*   **檔案**: `frontend/src/components/BriefForm.vue` (約在第 95 行 `handleSubmit`)
*   **操作**:
    1.  在 `submitData` 物件中，移除 `word_limit` 欄位。
    2.  確保 `optimization_mode` 仍然存在並正確對應 (例如 `'CONCISE'`, `'STANDARD'`, `'DETAILED'`)。
*   **驗證**: 在瀏覽器開發者工具的 Network 面板，點擊生成後檢查 Payload。
    *   ✅ **Pass**: Payload 包含 `optimization_mode`，**不包含** `word_limit`。

#### Step 1.3: 清理 API 驗證邏輯
*   **檔案**: `frontend/src/api.js`
*   **操作**:
    1.  搜尋 `word_limit` 驗證邏輯 (約在第 61 行)。
    2.  刪除相關程式碼。
*   **驗證**: 前端代碼編譯無錯誤 (`npm run build` 或檢查 console)。

---

### 🟡 第二階段：後端模板與邏輯驗證 (Backend Verification)

**目標**: 確認後端定義正確，且舊邏輯不會被觸發。

#### Step 2.1: 驗證模板定義
*   **檔案**: `src/functions/utils/prompt_builder.py`
*   **操作**: 檢查 `TEMPLATE_DESCRIPTIONS` 字典。
*   **檢查清單**:
    *   [ ] `concise`: `length_guide` 為 "40-120字"。
    *   [ ] `standard`: `length_guide` 為 "130-230字"。
    *   [ ] `detailed`: `length_guide` 為 "280-550字"。
    *   [ ] 每個模板的 `content_guide` 內容有顯著差異 (簡短 vs 平衡 vs 詳細分段)。
*   **驗證**: 確認無誤後，進行下一步。

#### Step 2.2: 驗證 Prompt 組裝邏輯
*   **檔案**: `src/functions/utils/prompt_builder.py` (函數 `build_generate_prompt`)
*   **操作**: 檢查程式碼是否正確讀取 `optimization_mode` 並注入對應的 `content_guide`。
*   **檢查點**: 
    *   確認 `mode_key` 邏輯能正確處理大小寫 (如前端傳 `CONCISE`，後端轉 `concise`)。

#### Step 2.3: 驗證舊版邏輯隔離
*   **檔案**: `src/langgraph_state/state.py` (函數 `finalize_state`)
*   **操作**: 檢查約第 492 行的 `if word_limit:` 區塊。
*   **確認**:
    *   該區塊存在 (保留作為 API 相容性)。
    *   因為前端不再傳 `word_limit`，此區塊在正常流程中**不會被執行**。
    *   這意味著系統將完全依賴 Prompt 層控制，符合預期。

---

### 🔴 第三階段：整合測試 (Integration Test)

**目標**: 執行端到端測試，確保全流程運作正常。

#### Step 3.1: 執行 E2E 測試腳本
*   **指令**:
    ```bash
    cd /home/ubuntu/projects/OrganBriefOptimization
    python scripts/test_e2e_with_llm.py
    ```
*   **預期行為**:
    *   腳本會發送 30 個請求 (10 個案例 × 3 種模板)。
    *   注意觀察輸出的 JSON Payload 是否**沒有** `word_limit`。

#### Step 3.2: 分析測試結果
*   **檢查項目**:
    1.  **API 成功率**: 必須 30/30 (100%)。
    2.  **字數合規性**:
        *   CONCISE: 平均 ≤ 110 字。
        *   STANDARD: 平均 ≤ 230 字。
        *   DETAILED: 平均 ≤ 550 字。
    3.  **無截斷符號**: 檢查 `body_html` 結尾是否**沒有** `...`。
    4.  **模板差異**: 確認 `detailed` 字數明顯大於 `concise`。

#### Step 3.3: 產出報告
*   確認測試腳本生成的 `stage3_e2e_results_*.json` 和 Excel 報告。
*   如果所有檢查通過，則標記此階段完成。

---

## 🏁 完成標準 (Definition of Done)

1.  [ ] 前端無 `word_limit` 輸入框。
2.  [ ] API 請求 Payload 不包含 `word_limit`。
3.  [ ] 後端 Prompt 正確根據模板注入字數要求。
4.  [ ] E2E 測試 30 次呼叫全部成功，且字數符合模板規範。
