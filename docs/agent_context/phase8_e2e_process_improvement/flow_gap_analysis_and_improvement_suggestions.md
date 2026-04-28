# 公司簡介生成API流程差距分析與改進建議

## 一、流程比較表（目前 vs 期望）

| 流程步驟 | 目前實現 | 用戶期望流程 | 差距說明 |
|---------|----------|--------------|----------|
| 1. 輸入處理 | 接收 organNo, organ, mode, 可選 companyUrl | 公司提供素材 (organ 基本資訊) | 基本一致，但用戶期望的「素材」範圍更廣 |
| 2. API調用 | POST /v1/company/profile/process | 調用api | 一致 |
| 3. 網路搜尋 | 未提供 companyUrl 時，使用 organ 名稱搜尋 `"{organ} 官網"` | API根據素材上網搜尋 | 基本一致，但目前僅搜尋官網，未考慮其他相關資訊 |
| 4. 搜尋結果判斷 | 搜尋到結果 → 使用第一個URL<br>未搜尋到結果 → 拋出 ExternalServiceError 錯誤 | 有搜到就跟素材一起給llm生成<br>沒搜到就只有素材給llm生成 | **主要差距**：目前失敗路徑直接拋錯誤，期望中應該有備用路徑 |
| 5. 內容擷取 | 從目標 URL 擷取主要內容 | (隱含在搜尋結果處理中) | 目前實現中存在，但未在期望流程中明確提及 |
| 6. Prompt 建構 | 使用擷取內容 + organ 建構 Prompt | 將搜尋結果（若有）和素材一起送給 LLM<br>僅使用素材送給 LLM (當無搜尋結果時) | **差距**：目前無備用路徑，僅在有內容時運作 |
| 7. LLM 生成 | 呼叫 LLM 取得公司簡介 | LLM 生成公司簡介 | 一致 |
| 8. 後處理 & 返回 | 後處理後返回結果 | 返回llm結果給前端 | 基本一致 |
| 9. 錯誤處理 | 無 URL 時直接失敗 (ExternalServiceError) | 永不應該因找不到網站內容而失敗，應該有備用生成路徑 | **核心差距**：缺乏容錯機制 |

## 二、差距根因分析

### 1. 核心問題：缺乏備用生成路徑
- **位置**：`src/functions/utils/generate_brief.py` 第22-31行
- **具體表現**：當 `url_candidates` 為空且未提供 `companyUrl` 時，直接拋出 `ExternalServiceError`
- **根因**：設計假設必須能夠取得公司網站內容才能生成簡介，沒有考慮純文字輸入的場景

### 2. 次要問題：搜尋策略過於狹窄
- **位置**：`src/functions/utils/web_search.py` (從分析中推斷)
- **具體表現**：搜尋查詢格式固定為 `"{company_name} 官網"`，可能遺漏其他有價值的資訊來源
- **根因**：過度依賴官網作為主要資訊來源，未考慮多元搜尋策略

### 3. 架構問題：缺乏模組化的資料採集與融合
- **位置**：整個 generate_brief 流程
- **具體表現**：資料採集（搜尋+擷取）、Prompt 建構、LLM 呼叫緊密耦合
- **根因**：功能未按照建議的管線架構進行分離，導致難以插入備用路徑或擴展資料來源

### 4. 用戶體驗問題：錯誤訊息不夠友善
- **位置**：`src/functions/utils/generate_brief.py` 第29-31行
- **具體表現**：錯誤訊息要求用戶提供 companyUrl 或確保搜尋有結果，但未提供備用方案
- **根因**：錯誤處理著重於失敗通報而非提供替代方案

## 三、改進路線圖

### 階段 1：實施備用生成路徑（P0 - 立即執行）
**目標**：確保API永遠不會因找不到網站內容而失敗
**時間估計**：1-2 天

### 階段 2：優化錯誤處理與日誌（P0 - 與階段1並行）
**目標**：使備用路徑的執行也能被適當追蹤和記錄
**時間估計**：1 天

### 階段 3：整合結構化公司資料來源（P1 - 短期）
**目標**：提升生成簡介的準確性和專業度
**時間估計**：3-5 天

### 階段 4：增強 Prompt 智慧（P1 - 中期）
**目標**：根據可用資料品質動態調整生成策略
**時間估計**：2-3 天

### 階段 5：添加品質控制機制（P2 - 長期）
**目標**：確保輸出符合最低品質標準
**時間估計**：2-3 天

## 四、技術實施建議

### 1. 階段1：實施備用生成路徑 (P0)

**修改位置**：`src/functions/utils/generate_brief.py`

**具體改動**：
```python
def generate_brief(data):
    organ = data['organ']
    company_url = data.get('companyUrl')

    # Step 1: query URL candidates (use organ name for search)
    url_candidates = web_search(organ, company_url)
    
    # Determine if we have web content to work with
    has_web_content = bool(url_candidates) or bool(company_url)
    
    if has_web_content:
        # 原有路徑：有網站內容時的處理流程
        if url_candidates:
            target_url = url_candidates[0]
        elif company_url:
            target_url = company_url
        else:
            # 此理論上不應該發生，因為已檢查過 has_web_content
            target_url = None
            
        if target_url:
            # Step 2: extract content from target URL
            try:
                raw_content = extract_main_content(target_url)
            except Exception as exc:
                raise ExternalServiceError('failed to fetch company website content') from exc
            
            # 3. 前處理
            clean_text = preprocess_text(raw_content)
            # 4. Prompt 組裝
            prompt = build_generate_prompt(organ, clean_text)
        else:
            # 備用路徑：只有公司名稱時的處理流程
            clean_text = organ  # 只使用公司名稱作為輸入
            # 4. Prompt 組裝 (使用備用 Prompt)
            prompt = build_generate_prompt_fallback(organ)
    else:
        # 完全備用路徑：連公司名稱搜尋都失敗時（理論上不應該發生）
        clean_text = organ
        prompt = build_generate_prompt_fallback(organ)
    
    # 5. 呼叫 LLM
    llm_result = call_llm(prompt)
    # 6. 後處理
    return post_process(llm_result)
```

**新增函式**（在同一文件末尾或 prompt_builder.py）：
```python
def build_generate_prompt_fallback(organ):
    """當無法取得任何網路資訊時，僅基於公司名稱生成簡介"""
    return f"""請基於公司名稱「{organ}」生成一段專業的公司簡介。由於缺乏具體的公司資訊，請：
1. 以專業、中性的口吻描述這可能是一家什麼樣的公司
2. 提供一個合理的、通用的公司結構描述
3. 保持內容簡潔但專業
4. 明確指出此為基於有限資訊的生成結果
5. 字數控制在100-300字之間"""
```

### 2. 階段2：優化錯誤處理與日誌 (P0)

**修改位置**：`src/functions/utils/generate_brief.py` 和相關日誌記錄

**具體改動**：
- 在備用路徑執行時記錄 INFO 級別日誌，指出正在使用備用生成路徑
- 在回應中加入品質指標，例如：`dataQuality: "limited"` 或 `dataSource: "fallback-only"`
- 修改 error_handler.py 中的 ExternalServiceError，使其在適當情況下不被拋出

### 3. 階段3：整合結構化公司資料來源 (P1)

**架構建議**：參考 workflow 分析中的建議架構

**實施步驟**：
1. 創建新的資料採集器模組：`src/functions/utils/data_collector.py`
2. 實施多來源採集策略：
   - 優先級 1：結構化公司資料 API (如台灣公司註冊資料)
   - 優先級 2：公司網站內容擷取 (現有實現)
   - 優先級 3：基於公司名稱的網路搜尋摘要 (現有實現的變體)
3. 創建資料融合器：`src/functions/utils/data_fusion.py`
4. 更新 generate_brief 以使用新的採集和融合管線

### 4. 階段4：增強 Prompt 智慧 (P1)

**實施建議**：
1. 在 prompt_builder.py 中創建多種 Prompt 模板：
   - `build_generate_prompt_high_quality()`：當有豐富結構化資料時
   - `build_generate_prompt_medium_quality()`：當有網站內容但結構化資料有限時
   - `build_generate_prompt_low_quality()`：當只有基本公司資訊時 (備用路徑)
   - `build_generate_prompt_fallback()`：當幾乎無任何資訊時
2. 創建資料豐富度評估函式
3. 根據評估結果動態選擇適當的 Prompt 建構函式

### 5. 階段5：添加品質控制機制 (P2)

**實施建議**：
1. 創建品質檢查器：`src/functions/utils/quality_checker.py`
2. 實施檢查規則：
   - 必要元素檢查：公司名稱必須出現
   - 長度適切性：符合指定的字數限制
   - 基本語言品質：無明顯錯誤、流暢度
   - 事實一致性：與來源資料不矛盾 (當有來源時)
3. 在後處理階段加入品質檢查
4. 對於不達標的結果，提供自動重試或標記機制

## 五、優先級排序

| 優先級 | 項目 | 說明 | 預估工作量 |
|--------|------|------|------------|
| **P0** | 實施備用生成路徑 | 確保API永不因找不到網站內容而失敗 | 1-2 天 |
| **P0** | 優化錯誤處理與日誌 | 追蹤備用路徑執行並提供適當回饋 | 1 天 |
| **P1** | 整合結構化公司資料來源 | 提升生成品質的基礎設施 | 3-5 天 |
| **P1** | 增強 Prompt 智慧 | 根據資料品質動態調整生成策略 | 2-3 天 |
| **P2** | 添加品質控制機制 | 確保輸出符合最低品質標準 | 2-3 天 |
| **P3** | 實施快取機制 | 提升重複請求的效能 | 1-2 天 |
| **P3** | 加入A/B測試框架 | 支援不同Prompt策略的比較 | 2-3 天 |

## 六、關於「可以直街寫成agent並調用對應的mcp或function call」建議的評估

### 可行性評估：**高度可行**

### 實現方式：

1. **Agent 架構設計**：
   - 創建公司簡介生成 Agent，封裝完整的決策流程
   - Agent 內部包含：
     * 資料採集工具 (web search, 結構化資料 API)
     * 內容擷取工具
     * Prompt 建結工具
     * LLM 呼叫工具
     * 品質檢查工具

2. **MCP/Function Call 實現**：
   - 將每個功能模組實現為可被 Agent 調用的 Function：
     ```
     Functions:
     - web_search_company(organ_name: str, company_url: Optional[str]) -> List[str]
     - extract_website_content(url: str) -> str
     - preprocess_text(raw_text: str) -> str
     - build_prompt(organ: str, content: str, data_quality: str) -> str
     - call_llm(prompt: str) -> str
     - post_process(brief: str) -> str
     - check_quality(brief: str, source_data: str) -> QualityScore
     ```
   - Agent 使用決策邏輯來選擇適當的函式組合

3. **優勢**：
   - 更清晰的職責分離
   - 更容易測試和維護個別組件
   - 更靈活的流程控制（可輕鬆插入/移除步驟）
   - 更好地符合微服務和雲端原生架構
   - 便於未來擴展（添加新的資料來源或處理步驟）

4. **實現建議**：
   - 短期：在現有框架內實施備用路徑（如上述方案）
   - 中期：逐步重構為 Agent 架構
   - 長期：完全採用 Agent + Function Call 模式

## 七、結論

目前實施與用戶期望流程的主要差距在於缺乏備用生成路徑——當無法取得公司網站內容時，系統直接失敗而非嘗試僅使用提供的基本資料生成簡介。這不僅影響系統穩定性，也提供了不佳的用戶體驗。

透過實施備用生成路徑（P0 優先級），可以立即解決這個核心問題，確保API在各種情況下都能返回結果。之後的改進階段則可以逐步提升生成品質、架構清晰度和系統可維護性。

建議採用階段性實施方式，先確保基本功能的穩定性（備用路徑），再逐步優化品質和架構，最終可考慮演進為更彈性的 Agent-based 架構。