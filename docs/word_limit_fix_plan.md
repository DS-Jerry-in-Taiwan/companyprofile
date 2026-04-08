# 公司簡介產生系統 — 字數限制修復開發規劃

## 一、背景與現有問題說明

### 1. 現狀與問題摘要
- 前端允許設定字數限制（word_limit，50-2000）。
- 後端目前僅於 prompt 加提示“請生成200-300字”，而未真正根據用戶輸入字數限制調整生成。
- 語言模型（LLM）API 層未根據 word_limit 動態配置 max_output_tokens，僅用預設4096。
- 用戶即使填 50 字，實際回傳仍可能數百字，且前後端無二次截斷保證。

### 2. 業務影響
- 使用者期望精準控制公司簡介長度無法實現。
- 超長回應造成閱讀負擔及部分應用場景不適用。

## 二、技術方案與流程設計

### 1. 處理流程總覽

1. 用戶於前端填寫/選擇字數限制（50-2000），資料隨表單傳送 word_limit 給後端。
2. API 校驗 word_limit 合法性。
3. prompt 組裝時，將動態顯示『請根據上述資訊，生成公司簡介（{word_limit}字以內）』，不是寫死200-300。
4. 語言模型（LLM）API 呼叫動態 max_output_tokens，計算方式：max_output_tokens = min(word_limit * 2, 4096)。
5. LLM 回傳字串，後端自動執行字數截斷（超過則截斷至 word_limit，建議用中文字數/UTF-8長度切片）。
6. 最終回傳給前端的 brief/body_html，字數必 <= word_limit。

流程示意圖：

用戶輸入（word_limit）
→ 前端傳遞
→ API 校驗
→ prompt_builder（生成動態字數描述）
→ LLMService（max_output_tokens 動態配置）
→ 回應截斷（enforce 字數）
→ 回傳

### 2. 修正重點
- prompt_builder.py：prompt 字數描述動態帶入 word_limit。
- llm_service.py & services/llm_service.py：將 word_limit 轉 token 傳入生成API。
- generate_brief.py 等處後處理：根據 word_limit 對 output 嚴格截斷。
- 所有欄位驗證與例外，輸入非法應報錯並中斷處理。

## 三、主要檔案與模組職責

- frontend/src/components/BriefForm.vue：表單與 word_limit 欄位傳遞。
- src/functions/utils/prompt_builder.py：生成 prompt，負責組裝文字說明（公司簡介長度指示...）。
- src/functions/utils/llm_service.py：轉交 word_limit 為 max_output_tokens，呼叫模型服務。
- src/services/llm_service.py：Google Gemini/gemini-2.5-flash API 實際呼叫，config設置 max_output_tokens 並做自動截斷判斷。
- src/functions/utils/generate_brief.py：主服務流程，調用後保證輸出字數不超出配置。
- 測試：tests/下相關生成與回歸測試。

## 四、API Input/Output 樣例

**（Input）**
```json
{
  "organ": "ABC科技股份有限公司",
  "organNo": "12345678",
  "word_limit": 100,
  ...
}
```

**（Output）**
```json
{
  "title": "ABC科技 — 智慧創新先驅",
  "body_html": "<p>ABC科技...（最長100字，已自動截斷）</p>",
  "summary": "專精AI應用與服務。"
}
```

## 五、開發及測試建議

- 單元測試（pytest）：覆蓋 word_limit edge cases（50, 100, 2000, 非法值...）。
- e2e測試：實際填寫字數限制生成公司簡介，驗證 API 回應字數未超出。
- 錯誤注入測試：輸入非法限值（如 'abc', 0, 4000）應報錯。
- 模型回覆長度遇超出 word_limit，確保後端自動truncate。

## 六、開發與驗證/啟動說明

1. 實作並提交後，於本地執行 `pytest tests/`。
2. 前端可手動於表單測試不同字數限制送出。
3. 若部署 staging/UAT，建議持續監控，確保未再出現過長產出。
4. 確認功能上線後同步補齊 docs/

---

如需調整內容，請留言，確認後會建立此 md 檔案於 docs/word_limit_fix_plan.md。
