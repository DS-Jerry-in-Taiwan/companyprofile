# 字數限制優化計劃 (Content Length Optimization Plan)

**日期**: 2026-04-13  
**狀態**: 📋 待 Architect 審核與調整  
**優先級**: P1（影響用戶體驗）  
**相關優化項目**: #5 字數限制、#8 模板2簡潔、#10 模板差異

---

## 1. 問題描述

### 1.1 現況分析

目前的字數限制實現存在以下問題：

| 組件 | 當前行為 | 問題 |
|------|---------|------|
| `prompt_builder.py` | ✅ 已在 prompt 中告知 LLM 字數範圍 | LLM 有時不遵守 |
| `template_differentiator.py` | ❌ 強制截斷 + 加 `...` | 內容被截斷得很生硬，破壞語意完整性 |
| `_truncate_html_content()` | 逐標籤累加，超過時截斷文字 + `...` | 可能截斷在半句話中間 |
| `_truncate_plain_text()` | 找句號截斷，無句號時直接截斷 + `...` | 有時仍會截斷不自然 |

### 1.2 用戶體驗問題

1. **截斷突兀**：用戶看到完整的句子突然被截斷，加上 `...`，感覺內容不完整
2. **風格破壞**：LLM 精心生成的內容被後處理截斷，失去原有的表達風格
3. **資訊遺失**：重要資訊可能剛好落在截斷點之後

### 1.3 根本原因

目前的架構是「LLM 生成 → 後處理截斷」，這是一種被動式的字數控制。更好的方式應該是「Prompt 層控制 → LLM 生成符合長度的內容 → 輕量驗證」。

---

## 2. 優化方案

### 2.1 核心思路

```
【目前架構】
API → Prompt（告知字數）→ LLM 生成 → 強制截斷模組 → 輸出
                                          ↑ 問題所在

【優化後架構】
API → Prompt（明確字數範圍）→ LLM 生成 → 字數檢核模組 → 若超出 range → 要求 LLM 重寫（保留風格與意涵）
                                                      ↓ 若在 range 內
                                                    直接輸出
```

### 2.2 具體實施步驟

#### 步驟 1：強化 Prompt 層的字數控制（`prompt_builder.py`）

**當前狀態**：已有基本的字數提示，但 LLM 有時不遵守。

**優化方向**：
- 在 prompt 中更明確地強調字數限制
- 加入「生成後自我檢查」的指令
- 提供字數範圍的上下限（而非只有上限）

**修改位置**：`src/functions/utils/prompt_builder.py` 的 `TEMPLATE_DESCRIPTIONS` 和 `build_generate_prompt()`

#### 步驟 2：新增字數檢核模組（新建 `word_count_validator.py`）

**功能**：
- 檢查 LLM 生成的內容是否在目標字數範圍內
- 若超出範圍（例如超過上限 20%），觸發重寫流程
- 若在可接受範圍內，直接通過

**重寫策略**：
- 保留原有的風格與意涵
- 只做「文字縮放」（text scaling）：精簡冗餘描述、合併句子、移除修飾詞
- 不改變核心資訊和表達角度

#### 步驟 3：簡化/移除強制截斷模組（`template_differentiator.py`）

**當前狀態**：`differentiate_template()` 函數負責截斷。

**優化方向**：
- 移除 `_truncate_html_content()` 和 `_truncate_plain_text()` 中的截斷邏輯
- 改為只做「輕量驗證」：若字數超出可接受範圍，記錄警告但不強制截斷
- 最終由字數檢核模組處理超出情況

#### 步驟 4：整合到 LangGraph 流程（`company_brief_graph.py`）

**修改位置**：
- 在 `finalize_state()` 中，先呼叫字數檢核
- 若需要重寫，呼叫 LLM 進行縮放生成
- 若不需要，直接輸出

### 2.3 字數範圍定義

| 模板 | 當前 Prompt 提示 | 建議檢核範圍 | 觸發重寫閾值 |
|------|----------------|-------------|-------------|
| Concise | 50-100 字 | 40-120 字 | >120 字 |
| Standard | 150-200 字 | 130-230 字 | >230 字 |
| Detailed | 300-500 字 | 280-550 字 | >550 字 |

---

## 3. 需要調整的工作規劃

### 3.1 工作項目調整

| 原工項 | 調整後工項 | 負責 Agent | 預估工時 |
|--------|-----------|-----------|---------|
| Agent F/G Phase 2: 內容多樣化 | Agent F/G Phase 2: 內容多樣化 + 字數控制優化 | Agent F/G | 2→3 天 |
| Agent F/G Phase 3: 模板差異化 | Agent F/G Phase 3: 模板差異化（配合新字數控制） | Agent F/G | 1→1.5 天 |
| （無） | 新建 `word_count_validator.py` 模組 | Agent B | 1 天 |
| （無） | 整合測試：驗證字數控制效果 | Agent F/G | 0.5 天 |

### 3.2 需要修改的文件清單

| 文件路徑 | 修改類型 | 修改內容 |
|---------|---------|---------|
| `src/functions/utils/prompt_builder.py` | 修改 | 強化字數提示、加入生成後自我檢查指令 |
| `src/functions/utils/template_differentiator.py` | 修改 | 移除強制截斷邏輯，改為輕量驗證 |
| `src/functions/utils/word_count_validator.py` | **新建** | 字數檢核模組（含重寫觸發邏輯） |
| `src/langgraph_state/state.py` | 修改 | 新增 `word_count_check` 相關欄位 |
| `src/langgraph_state/company_brief_graph.py` | 修改 | 在 `finalize_state()` 中整合字數檢核 |
| `tests/test_word_count_validator.py` | **新建** | 字數檢核單元測試 |
| `tests/test_template_differentiator.py` | 修改 | 更新測試反映新設計 |
| `tests/test_template_integration.py` | 修改 | 新增字數控制相關測試 |
| `docs/agent_context/phase14_functionality_recovery/PROGRESS_TRACKING.md` | 修改 | 更新進度記錄 |
| `docs/agent_context/phase14_functionality_recovery/phase14_planning.md` | 修改 | 更新階段二計劃 |
| `docs/agent_context/phase14_functionality_recovery/05_validation_checklist.md` | 修改 | 新增字數控制驗收標準 |

---

## 4. 實施優先級與時程

### 4.1 優先級排序

1. **P0 - 立即執行**：強化 Prompt 層字數控制（影響最大，風險最低）
2. **P1 - 短期執行**：新建字數檢核模組
3. **P2 - 中期執行**：簡化強制截斷模組
4. **P3 - 整合測試**：端到端驗證

### 4.2 預估時程

| 階段 | 工作內容 | 開始日期 | 完成日期 | 工時 |
|------|---------|---------|---------|------|
| 1 | 強化 Prompt 層字數控制 | 2026-04-14 | 2026-04-14 | 0.5 天 |
| 2 | 新建字數檢核模組 | 2026-04-14 | 2026-04-15 | 1 天 |
| 3 | 簡化強制截斷模組 | 2026-04-15 | 2026-04-15 | 0.5 天 |
| 4 | 整合到 LangGraph 流程 | 2026-04-15 | 2026-04-16 | 1 天 |
| 5 | 單元測試與整合測試 | 2026-04-16 | 2026-04-16 | 1 天 |
| **總計** | | | | **4 天** |

---

## 5. 風險評估

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|---------|
| LLM 重寫後仍超出範圍 | 中 | 低 | 設定最大重寫次數（2次），超過則接受當前結果 |
| 重寫改變原有風格 | 中 | 中 | 在重寫 prompt 中明確要求保留風格與意涵 |
| 增加 API 呼叫次數 | 低 | 中 | 只在超出範圍時觸發重寫，預期 <10% 案例需要 |
| 現有測試失敗 | 低 | 低 | 更新測試用例反映新設計 |

---

## 6. 驗收標準

| 指標 | 目標 | 測量方式 |
|------|------|---------|
| Concise 模板字數 | 40-120 字 | 端到端測試 10 案例，100% 達標 |
| Standard 模板字數 | 130-230 字 | 端到端測試 10 案例，100% 達標 |
| Detailed 模板字數 | 280-550 字 | 端到端測試 10 案例，100% 達標 |
| 無突兀截斷 | 0 案例出現 `...` 截斷 | 人工審查 10 案例 |
| 風格保留 | 重寫前後語意相似度 >0.8 | 自動化語意相似度計算 |
| API 呼叫增加 | <10% 案例需要重寫 | 端到端測試統計 |

---

## 7. 技術細節

### 7.1 字數檢核模組設計（`word_count_validator.py`）

```python
class WordCountValidator:
    """字數檢核器"""
    
    RANGES = {
        "concise": (40, 120),
        "standard": (130, 230),
        "detailed": (280, 550),
    }
    
    def validate(self, html_content: str, template_type: str) -> ValidationResult:
        """檢核字數是否在範圍內"""
        ...
    
    def needs_rewrite(self, result: ValidationResult) -> bool:
        """判斷是否需要重寫"""
        ...
    
    def build_rewrite_prompt(self, original_content: str, template_type: str, 
                             current_length: int, target_range: tuple) -> str:
        """建構重寫 prompt，要求保留風格與意涵，只做文字縮放"""
        ...
```

### 7.2 重寫 Prompt 設計

```
請將以下公司簡介進行文字縮放，使其字數符合 {target_range} 的範圍。

【原始內容】（{current_length} 字）
{original_content}

【要求】
1. 保留原有的核心資訊和表達風格
2. 只進行文字縮放：精簡冗餘描述、合併句子、移除不必要的修飾詞
3. 不要改變敘述角度和語氣
4. 確保 HTML 標籤結構完整
5. 最終字數請控制在 {target_range} 之間
```

---

## 8. 參考文件

- `PROGRESS_TRACKING.md` - Phase 14 進度追蹤
- `TEMPLATE_DIFFERENTIATION_FIX_PLAN.md` - 模板差異化修復計劃
- `Fewshot_Validation_Implementation_Summary.md` - Few-shot 驗證實施總結
- `phase14_planning.md` - Phase 14 整體計劃

---

**文件建立**: 2026-04-13  
**待 Architect 審核**: 請根據此分析報告調整工作項目規劃  
**下一步**: Architect 審核後，分配給對應 Agent 執行

(End of file)
