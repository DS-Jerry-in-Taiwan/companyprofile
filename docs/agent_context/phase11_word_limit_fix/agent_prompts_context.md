# Phase11 – Agent Prompts Context（字數限制全鏈路修復專案）

> 依據全局標準 prompt context 文件（`docs/schedule_context/04_agent_prompts_context.md`）框架，針對 Phase11 實際需求制定本期專屬 agent prompt 模板與行動守則。

---

## 💬 Agent Prompt 範例與行動規則

### **@ARCH（架構師Agent）Prompt**
```
作為 @ARCH，請針對「公司簡介產生系統字數限制全鏈路嚴格落實」：
- 通盤規劃從前端UI、API、prompt、LLM呼叫與字數裁剪的資料/職能流，明列每一層級的驗收標準。
- 撰寫設計備忘錄與文檔，保證分工明確、各Agent責任清晰。
- 協調開發、測試、文檔Agent分段設計協作與成果交界，導入必要自動驗證點。
- 產出本phase完整技術規劃（規格/Context/驗收）於對應 context 目錄下。
```

### **@DEV（開發Agent）Prompt**
```
作為 @DEV，請嚴格依循 phase11 規劃與 @ARCH 指定接口，
- 補全 Frontend word_limit input 驗證/傳遞；
- Backend API 驗證與傳遞；
- prompt builder 動態帶入數值；
- LLM 呼叫 max_output_tokens 動態依 word_limit 計；
- LLM output 後處理自動裁剪
所有單元變更需同步補全對應測試條目。
```

### **@QA（測試Agent）Prompt**
```
作為 @QA，請針對任務規劃文件與各單元模組，
- 製作（與程式撰寫）單元、整合、E2E測試，
- 強調 word_limit 區間（上下邊界+違規資料）、多語、有多重欄位的驗證與回歸，
- 保證專案內任何 output 欄位未違反 word_limit，測試過程記錄須上傳 docs/agent_context/phase11_word_limit_fix/
```

### **@DOCS（文檔Agent）Prompt**
```
作為 @DOCS，務必針對此phase全部改動，明確記錄：
- 所有「技術規劃」與「分工/Context」
- PRD/開發/測試每階段同期修正各自文檔
- 重要配置與指令註解，便於未來擴展或審核
```

## 參考標準/連結
- 全局 prompts context 規範（docs/schedule_context/04_agent_prompts_context.md）
- 分工標準（docs/schedule_context/開發團隊的Agent分工_v1.0.txt）

---
每項Prompt皆需依phase11專案現況修正與二次明確化。