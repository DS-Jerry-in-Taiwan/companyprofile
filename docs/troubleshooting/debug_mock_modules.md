# Debug Mock Modules 任務彙整

## 目標
針對專案中尚未串接真實服務、仍為 mock（假資料）的模組進行排查、紀錄與後續開發追蹤。

---

## 1. Mock 模組狀態（已更新：2026-03-30）

### (A) LLM 服務 ✅ 已完成
- 檔案：`src/functions/utils/llm_service.py`
- 函數：`call_llm(prompt)`
- 狀態：✅ 已串接真實 Gemini API
- 實作：使用現有 `src/services/llm_service.py` 的 `LLMService`
- 測試：成功生成公司簡介

### (B) Web Search 服務 ✅ 已完成
- 檔案：`src/functions/utils/web_search.py`
- 函數：`web_search(company_name, company_url=None)`
- 狀態：✅ 已串接真實 Serper.dev API
- 實作：使用現有 `src/services/serper_search.py` 的 `SerperSearchProvider`
- 測試：成功搜尋並返回真實 URL

### (C) 其他模組
- `text_preprocessor.py`：僅做 strip，無進階清洗

---

## 2. 整合測試結果

### LLM API 測試
```
Title: 揚才文理補習班：深耕教育十餘載，以「適性揚才」成就國高中升學夢想
Summary: 深耕林口十餘載，秉持適性揚才理念，提供國高中精緻小班與客製化家教的專業升學領導品牌。
Status: ✅ 正常
```

### Web Search API 測試
```
https://www.tsmc.com/chinese
https://esg.tsmc.com/
https://www.taiwansemi.com/
Status: ✅ 正常
```

### OPTIMIZE 模式測試
```
原始: 揚才補習班，自民國99年創立以來...
優化後: 私立揚才文理短期補習班成立於民國99年，深耕大林口與龜山地區超過十載...
Status: ✅ 正常
```

---

## 3. Agent 執行指令（Debug/開發流程）

### 檢查 API 狀態
```bash
# 測試 LLM
python -c "from src.functions.utils.llm_service import call_llm; print(call_llm('test'))"

# 測試 Web Search
python -c "from src.functions.utils.web_search import web_search; print(web_search('台積電'))"
```

### 測試完整流程
```bash
curl -X POST http://127.0.0.1:5000/v1/company/profile/process \
  -H "Content-Type: application/json" \
  -d '{"organNo": "69188618", "organ": "私立揚才文理短期補習班", "brief": "...", "mode": "OPTIMIZE"}'
```

---

> 本文件已更新：Mock 模組已全部串接真實 API (2026-03-30)