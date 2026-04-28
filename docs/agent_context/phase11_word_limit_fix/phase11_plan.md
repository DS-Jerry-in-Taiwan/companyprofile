# Phase11 公司簡介產生系統「字數限制」徹底修復開發規劃

## 一、背景與現有系統問題

### 1. 需求來源與現有流程問題
- 需求：使用者在產生公司簡介時，可以透過 UI 自訂要產生的最長字數（word_limit, 50~2000 字）。實際產出必須嚴格符合該限制。
- 現況：
    - 前端僅通過輸入規則檢查 word_limit 並傳給後端。
    - backend 在 prompt 只把字數需求當做純文字寫進 LLM 提示（甚至是固定區間、非動態）；LLM API 沒有根據此參數動態設置 max_output_tokens。
    - 回傳的內容常常遠超過使用者指定的字數，且沒有任何後處理確保符合 word_limit。

### 2. 主要業務與技術風險
- 產生超長結果，嚴重違背用戶輸入期望，降低服務信賴度。
- 無嚴格校驗與截斷，容易被 downstream 應用誤用，增加合規、法遵與 UX 風險。


## 二、修正方案與具體設計

### 1. 標準資料流設計

1. 使用者填寫/選擇 word_limit（50~2000）於前端；隨表單傳回後端。
2. API 嚴格驗證 word_limit 合法性。
3. prompt builder 動態插入「請生成在{word_limit}字以內」字樣（不可硬編 200-300 字等固定區間）。
4. LLM（Gemini/generate_content）API 呼叫時，將 max_output_tokens 計算為 min(word_limit * 2, 4096) 動態帶入。
5. LLM 回傳內容後，後端再以實際中文字數執行截斷確保 <= word_limit（JSON 欄位如 body_html、summary 等）。
6. API 最終回傳時的所有內容保證沒有任何欄位超過 word_limit。UI 顯示端亦不得再追加任何說明文字。


### 2. 需修正模組
- frontend/src/components/BriefForm.vue：檢查與傳遞 word_limit，正確顯示錯誤
- src/functions/utils/request_validator.py：API 檢查 word_limit 屬性是否合法範圍（int, 50-2000）
- src/functions/utils/prompt_builder.py：prompt 設計動態帶入 word_limit 而非死值
- src/functions/utils/llm_service.py：將 word_limit 正確傳遞與映射給 LLM service
- src/services/llm_service.py：API 呼叫時據 word_limit 計算 max_output_tokens；回傳後嚴格對每個欄位做字數檢查與必要截斷
- src/functions/utils/generate_brief.py：主控流程整合
- tests/：所有產生相關自動化測試必須涵蓋上下限/異常/合法字數測資


### 3. 特別注意
- LLM API 產生的最大 tokens，不等同中文字數（多取約 2x 保守，不可用固定 4096）。
- 截斷時以「中文字數」為主而非長度或 bytes。
- 若 LLM 回傳內容本來就合格，則不得修改；僅超限時截斷末尾。
- 「說明」或「summary」等 summary 欄位如有字數限制需求，一併遵從 word_limit 規則。


## 三、I/O 與流程舉例

### （Input）
```json
{
  "organ": "盛盛股份有限公司",
  "word_limit": 120,
  ...
}
```

### （Output）
```json
{
  "title": "盛盛股份 智能轉型專家",
  "body_html": "<p>盛盛股份有限公司專精於智慧自動化...（此內容最長120字，嚴格程式裁切）</p>",
  "summary": "自動化解決方案領導品牌。"
}
```


## 四、自動化測試與驗證建議

- 單元測試（pytest）：涵蓋 word_limit 上下界、非法資料、自動裁切之各種邊界條件。
- E2E 測試：由前端填寫各類 word_limit 驗證回應精確度，UI 與 API 皆應一致。
- 故障處理：任何驗證失敗回傳明確錯誤碼/訊息，不應 silently fallback。
- 嚴禁目檔外溢（例如 LLMSummary/Body 仍出現超字數情況）。


## 五、開發驗收步驟

1. 工程師完成所有縱深修正、測試補齊後，於本地 branch 跑完自動測試。
2. 使用各種範例輸入於 Staging/UAT 驗證字數嚴格度、錯誤回饋正確性。
3. 確認完整功能與設計紀錄同步補齊 docs/agent_context/phase11_word_limit_fix/。

---
如需調整內容，請務必循正式變更流審核並增修此計畫文件。
