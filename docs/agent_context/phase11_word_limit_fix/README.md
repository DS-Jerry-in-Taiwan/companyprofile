# Phase 11 — 字數限制精準修復（word_limit_fix）

## 目標說明
- 覆蓋全流程，從前端收集 word_limit 傳遞、API 校驗、LLM 請求 max_output_tokens 動態設置，到後端回應自動截斷，確保所有產生內容字數「不超出」用戶設定門檻。
- 詳細規格與技術細節請參見 docs/word_limit_fix_plan.md。

## Agent 雙軌任務分工

### 1. 前端Agent
- 介面表單驗證與提示，動態傳遞 word_limit
- 處理所有欄位數字輸入校正、異常回饋

### 2. API/業務Agent
- 校驗 word_limit 合法性/範圍，負責將字段正確下傳
- 處理 parseInt 結果判別、API 層健壯性
- 異常處理時正確傳遞錯誤

### 3. LLM/ServiceAgent
- 使用 word_limit 轉換 max_output_tokens 傳遞 LLM
- 保障 API 回傳內容字數 truncate 或適當補充錯誤訊息

### 4. 測試驗收Agent
- 單元、e2e 與回歸測試覆蓋各極值/非法輸入
- 驗證任務交付之所有產出的字數皆嚴格受控

## Input/Output 樣本

**API Input**
```json
{
  "organ": "XYZ股份有限公司",
  "organNo": "65432109",
  "word_limit": 120
}
```

**API Output**
```json
{
  "body_html": "<p>XYZ...（120字內自動截斷）</p>",
  ...
}
```

## 技術說明與規範
- 必須貫穿所有環節（prompt組裝、LLM請求、post-process）
- max_output_tokens 設為 word_limit*2 與最大4096
- 強制truncate以中文字（或UTF-8）為基準
- 例外與錯誤需人性化提示及嚴謹日誌

## 開發建議與驗證步驟
1. 參閱 docs/word_limit_fix_plan.md 作為修正藍本
2. 各agent依責分進行
3. 完成後聯合測試覆蓋所有極端情境
4. 驗證交付是否每個場景都無超出user指定字數門檻
