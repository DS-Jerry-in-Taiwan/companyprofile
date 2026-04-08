# Phase11 Agent Context — 字數限制修復專案責任與任務劃分

## 1. 本階段目標
- 徹底貫徹使用者 word_limit 設定，全端流程保證：產出的介紹文字必不超過該數字。
- 除錯與測試，確保所有異常、邊界、回歸案例可程式控管。

## 2. Agent 分工與權責

| Agent/角色             | 職責                                                    |
|------------------------|---------------------------------------------------------|
| front-end dev          | UI word_limit 欄位校驗，訊息提示，正確傳給 API          |
| backend API engineer   | 檢查 word_limit 合法性（型別、範圍），失敗直接中止     |
| prompt builder         | prompt 必須動態帶入 word_limit（不可硬編）              |
| LLM service            | 依 word_limit 決定 max_output_tokens，正確帶入 API      |
| Post-process/back-end  | LLM 回傳如超 word_limit，後處理自動裁斷任一段落        |
| test/qa                | 自動化測試與邊界、異常狀況檢查回傳內容是否超字數        |

## 3. 流程與責任節點

1. 【前端】用戶選填 word_limit，區間 50~2000。若異常（非 int / 超範圍）即報錯。
2. 【API】驗證 word_limit 合法性，失敗則阻擋且回傳明確錯誤訊息、狀態碼。
3. 【Prompt Builder】prompt 中明確載明『請產生不超過 {N} 字』，動態 N 不可寫死。
4. 【LLM Service】呼叫 LLM API 時帶入 max_output_tokens = min(word_limit * 2, 4096)。
5. 【Post-process】回傳後如有欄位超字數以程式自動裁切，不做斷字添加。
6. 【Output】API 保證 title、body、summary 均未超 word_limit。

## 4. 範例 I/O 與流程

### Input
```json
{
    "organ": "昇陽自動化",
    "word_limit": 90
}
```
### Output
```json
{
    "title": "昇陽自動化 智慧工廠引領者",
    "body_html": "<p>昇陽自動化致力於提供...（最多90字 by程式自動截斷）</p>",
    "summary": "智慧工廠·專業團隊。"
}
```

## 5. 驗收 Checklist
- [ ] 不可再有任何欄位 output 超過 word_limit 字數
- [ ] UI、API、prompt、LLM API、回傳內容五處都已補齊 word_limit 控制
- [ ] 測試腳本涵蓋上下限、異常、非法資料 case 全面通過
- [ ] 邊界案例（如 50、2000、非整數、過大、過小）皆有自動化測試

---
（本 context 必須隨後續溝通、需求調整即時更新）
