# Phase 8 E2E 流程優化 - 規劃建議小結

## 一、專案背景與問題診斷

### 1.1 原始問題
- GENERATE 模式回傳 `failed to fetch company website content` 錯誤
- 原因：直接爬蟲方式（requests + BeautifulSoup）容易被目標網站阻擋（403/429）
- 錯誤處理分散在各模組，缺乏統一的 Fallback 機制

### 1.2 分析發現
| 面向 | 問題 | 影響 |
|------|------|------|
| 錯誤處理 | try-catch 分散在 4+ 模組，策略不一致 | 維護困難，異常時無法統一降級 |
| 爬蟲脆弱性 | 直接爬蟲依賴靜態配置，無智慧路由 | 易被反爬機制阻擋，無法自動適應 |
| Fallback 機制 | 某環節失敗即導致整體流程終止 | API 穩定性不足，用戶體驗差 |

---

## 二、需求流程對比（HackMD vs 目前實現）

### 用戶期望流程
```
公司提供素材 → API 調用 → 根據素材上網搜尋 
  → 有搜到：搜尋結果 + 素材 → LLM 生成
  → 沒搜到：只有素材 → LLM 生成
→ 返回結果給前端
```

### 目前實現問題
- 搜尋失敗 → 直接拋出 ExternalServiceError（無 Fallback）
- 完全依賴直接爬蟲，無備用資料來源
- 缺乏多級降級機制

---

## 三、解決方案比較

### 3.1 方案比較表

| 方案 | 開發時間 | 錯誤處理 | 爬蟲問題 | 推薦度 |
|------|----------|----------|----------|--------|
| **直接修改** | 3-5 天 | 部分改善 | 仍用爬蟲 | ⭐⭐ |
| **從零建 Agent** | 8-12 天 | 框架級統一 | 可重構 | ⭐⭐⭐ |
| **LangChain + Tavily** | 2 週 | 框架級統一 | API 替代 | ⭐⭐⭐⭐ |

### 3.2 選擇方案：LangChain + Tavily API

#### 為什麼選擇這個方案？
1. **錯誤處理**：LangChain 提供 `RunnableRetry` + `RunnableWithFallbacks` 宣告式配置
2. **爬蟲問題**：用 Tavily API 替代直接爬蟲，無需處理反爬機制
3. **時間節省**：預計節省 34% 開發時間（72h vs 140h）
4. **可擴展性**：為未來 LangGraph 整合打下基礎

---

## 四、已完成的實作

### 4.1 Tavily API 整合
| 檔案 | 說明 |
|------|------|
| `requirements.txt` | 新增 `tavily-python>=0.1.6` |
| `src/services/tavily_search.py` | Tavily API 服務提供者 |
| `src/functions/utils/tavily_client.py` | 簡化 Client（搜尋+內容提取一次搞定）|
| `src/functions/utils/generate_brief.py` | 改用 Tavily 替代傳統爬蟲 |

### 4.2 測試驗證
- ✅ API 服務正常啟動
- ✅ GENERATE 模式可正常回應（mock 模式）
- ✅ Fallback 機制正常運作

---

## 五、待完成項目

### 5.1 短期（立即需要）
- [ ] 設定真實的 `TAVILY_API_KEY` 環境變數
- [ ] 安裝依賴：`pip install tavily-python`
- [ ] 用真實 API Key 進行完整測試

### 5.2 中期（後續優化）
- [ ] 整合 LangChain 錯誤處理（`RunnableRetry` + `RunnableWithFallbacks`）
- [ ] 實作 LangGraph 狀態圖（條件邊實現動態路由）
- [ ] 將 Tavily 包裝為 LangChain Tool

### 5.3 長期（可選）
- [ ] 建立多級 Fallback 鏈（搜尋失敗 → 備用 LLM → 預設回應）
- [ ] 實作快取機制減少 API 呼叫
- [ ] 加入 A/B 測試框架

---

## 六、架構建議

### 6.1 最終目標架構
```
┌─────────────────────────────────────────────────────────┐
│                  LangGraph StateGraph                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌──────────┐    ┌──────────────┐    ┌──────────┐    │
│   │  START   │───▶│ Tavily Tool  │───▶│   LLM    │    │
│   └──────────┘    │  (搜尋+提取)  │    │ Generation│    │
│                   └──────────────┘    └──────────┘    │
│                        │                   │         │
│                        ▼                   ▼         │
│                   ┌──────────┐         ┌──────────┐    │
│                   │  ERROR?  │         │ QUALITY  │    │
│                   │  CHECK   │         │  CHECK   │    │
│                   └──────────┘         └──────────┘    │
│                        │                               │
│           ┌────────────┼────────────┐                  │
│           ▼            ▼            ▼                  │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│     │ RETRY N  │ │ FALLBACK │ │ DEFAULT  │            │
│     │ (max=3)  │ │  SEARCH  │ │ RESPONSE │            │
│     └──────────┘ └──────────┘ └──────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 6.2 關鍵改進點
1. **用 API 替代爬蟲**：Tavily API 一次搞定搜尋和內容提取
2. **框架級錯誤處理**：LangChain Retry + Fallback 機制
3. **條件邊路由**：LangGraph 根據錯誤類型動態選擇下一步

---

## 七、配置說明

### 7.1 環境變數
```bash
# 必須
TAVILY_API_KEY=your_api_key_here  # 從 https://tavily.com/ 取得

# 可選（已有）
SERPER_API_KEY=your_serper_key_here
GOOGLE_API_KEY=your_google_key_here
```

### 7.2 安裝依賴
```bash
pip install tavily-python
```

---

## 八、風險與緩解

| 風險 | 緩解措施 |
|------|----------|
| API 呼叫失敗 | Fallback 到備用搜尋或使用 mock 資料 |
| API 成本增加 | 設置 max_results 限制，實施快取機制 |
| 版本變更 | 鎖定版本，漸進升級 |
| 現有功能回歸 | 保留直接呼叫路徑，雙軌運行 |

---

## 九、驗收標準

- [ ] GENERATE 模式在有/無 companyUrl 時都能正常回應
- [ ] 錯誤發生時有適當的 Fallback 機制（不再直接 500 錯誤）
- [ ] 日誌清楚記錄使用了哪個資料來源（Tavily/Serper/Fallback）
- [ ] 新增元件單元測試覆蓋 > 80%
- [ ] 端到端測試通過率不降低

---

## 十、下一步行動

1. **設定 TAVILY_API_KEY**（需要您提供 API Key）
2. **進行完整測試**驗證 Tavily API 整合
3. **啟動 LangChain/LangGraph 整合**（可選，需另開工作項目）

---

## 十一、相關文件

- `generate_mode_failure_analysis.md` - GENERATE 模式失敗原因分析
- `company_brief_generation_workflow_analysis.md` - 需求流程分析
- `flow_gap_analysis_and_improvement_suggestions.md` - 流程差距分析
- `langchain_langgraph_refactoring_analysis.md` - LangChain/LangGraph 重構分析
- `agent_vs_direct_modification_analysis.md` - Agent vs 直接修改比較

---

*文件資訊*
- 建立日期：2026-04-01
- 專案階段：Phase 8 E2E 流程優化
- 依賴技術：Tavily API, LangChain, LangGraph, Python
