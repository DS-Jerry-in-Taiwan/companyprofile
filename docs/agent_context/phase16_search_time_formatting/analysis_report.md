# Phase 16 效能與模組分析報告

**文件版本**: v1.0.0  
**建立日期**: 2026-04-17  
**更新日期**: 2026-04-17  
**狀態**: 🔍 分析完成

---

## 📊 執行摘要

### 核心發現
1. **Phase 16 比 Phase 14 慢 120%**，但原因不是批次 vs 非批次
2. **兩個 Phase 都是「一次性批量查詢」**，只是複雜度不同
3. **Phase 16 的 Prompt 長 5.6倍**，導致處理時間大幅增加
4. **真正的批次查詢設計意圖沒有實現**

### 建議行動
1. 修正搜尋配置使用 `gemini_planner_tavily`
2. 重新執行效能測試
3. 考慮實現真正的平行批次查詢

---

## 🔍 測試結果對比

### 效能測試結果（5間公司平均）

| 項目 | Phase 14 (8欄位) | Phase 16 (4面向) | 差異 |
|------|-----------------|-----------------|------|
| **搜尋時間** | 4.81s | 10.49s | **+118.1%** |
| **Summary Node** | N/A | 0.10s | N/A |
| **總時間** | **4.81s** | **10.59s** | **+120.1%** |

### 測試公司
1. 台積電
2. 鴻海
3. 富邦金控
4. 誠品生活
5. Gogoro

### 測試環境
- 相同硬體與網路條件
- 每間公司測試1次
- 使用 `gemini_fewshot` 策略（錯誤配置）

---

## 🧩 模組分析

### Phase 14: GeminiFewShotSearchTool

#### 查詢方式
```python
# 一次性批量查詢 8個欄位
prompt = """你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊。

【輸出格式 - 請嚴格遵守 JSON 格式】
{
    "company_name": "公司名稱",
    "unified_number": "統一編號",
    "capital": "資本額",
    "founded_date": "成立時間",
    "address": "公司地址",
    "officer": "負責人",
    "main_services": "主要服務",
    "business_items": "營業項目"
}

請搜尋並回覆 JSON。"""
```

#### 特性
- **Prompt 長度**: 329字元
- **API 呼叫**: 1次
- **查詢類型**: 一次性批量查詢
- **輸出格式**: 8欄位 JSON

### Phase 16: GeminiFewShotSearchTool（錯誤配置）

#### 查詢方式
```python
# 一次性批量查詢 4個面向
prompt = """你是一個公司資訊搜尋專家。請搜尋「{company_name}」的詳細資訊，並以結構化 JSON 格式返回。

【核心任務】
根據搜尋結果，提取公司的四個面向的資訊，並以 JSON 格式輸出。

【輸出格式】
嚴格按以下 JSON 格式輸出（無須額外說明文本）：

```json
{
  "foundation": "品牌實力與基本資料（不超過 500 字）",
  "core": "技術產品與服務核心（不超過 500 字）",
  "vibe": "職場環境與企業文化（不超過 500 字）",
  "future": "近期動態與未來展望（不超過 500 字）"
}
```

【特別要求】
1. 信息準確性...
2. 字數控制...
3. 去重和合併...
4. 無法獲得的信息...
5. 語言和風格...

【輸出檢查清單】
- [ ] 返回有效的 JSON...
- [ ] 包含四個鍵...
- [ ] 每個值都是字符串類型...
- [ ] 每個值都不超過 500 字...
- [ ] 無編造信息...
- [ ] JSON 前後無額外文本說明"""
```

#### 特性
- **Prompt 長度**: 1,856字元（+464%）
- **API 呼叫**: 1次
- **查詢類型**: 一次性批量查詢
- **輸出格式**: 4面向 JSON

### 正確的 Phase 16 設計: GeminiPlannerTavilyTool

#### 查詢方式
```python
# 真正的批次查詢
# Step 1: Gemini 規劃查詢框架
planner_prompt = """你是一個公司資訊搜尋規劃專家。
任務：為「{company_name}」規劃搜尋框架。

【輸出格式 - 請嚴格遵守 JSON 格式】
{
    "company_name": "{company_name}",
    "queries": [
        {
            "field": "面向名稱",
            "query": "Tavily 搜尋查詢",
            "priority": 1-3（1最高）,
            "description": "為什麼要查這個"
        }
    ],
    "confidence": "高/中/低"
}

【面向定義】
- foundation: 品牌實力與基本資料
- core: 技術產品與服務核心
- vibe: 職場環境與企業文化
- future: 近期動態與未來展望"""

# Step 2: Tavily 批次執行多個查詢
for query in queries:
    result = tavily_search(query["query"])
    
# Step 3: 合併結果
```

#### 特性
- **API 呼叫**: 1 + N次（N = 查詢數量）
- **查詢類型**: 真正的批次查詢
- **輸出格式**: 合併後的結構化資料

---

## 🔎 關鍵洞察

### 1. 設計意圖 vs 實際實現

#### 設計意圖（批次查詢）
```
輸入: ["查詢1", "查詢2", "查詢3", "查詢4"]
處理: 平行/序列執行多個查詢
輸出: 合併的多個結果
```

#### 實際實現（一次性批量查詢）
```
輸入: "請查詢所有資訊"
處理: 單次查詢包含所有要求
輸出: 單一整合結果
```

### 2. 效能差異的真正原因

| 因素 | Phase 14 | Phase 16 | 影響 |
|------|----------|----------|------|
| **Prompt 長度** | 329字元 | 1,856字元 | **主要因素** |
| **處理複雜度** | 簡單提取 | 複雜整合 | 次要因素 |
| **API 呼叫** | 1次 | 1次 | 無差異 |
| **查詢類型** | 一次性批量 | 一次性批量 | 無差異 |

### 3. 配置錯誤問題

**當前配置**:
```json
"search": {
  "provider": "gemini_fewshot"  # ← 錯誤！應該用 gemini_planner_tavily
}
```

**正確配置**:
```json
"search": {
  "provider": "gemini_planner_tavily"  # ← 批次查詢
}
```

---

## 🚨 問題診斷

### 問題 1: 測試配置錯誤
- **測試使用**: `gemini_fewshot`（一次性批量）
- **應該使用**: `gemini_planner_tavily`（批次查詢）
- **影響**: 效能測試結果無效

### 問題 2: 設計誤解
- **預期設計**: 批次查詢多個問句
- **實際實現**: 一次性批量查詢
- **影響**: 效能優化目標無法達成

### 問題 3: Prompt 過度複雜
- **Phase 16 Prompt**: 1,856字元
- **最佳實踐**: 通常 < 1,000字元
- **影響**: 處理時間大幅增加

---

## 🛠️ 建議修正

### 修正 1: 更新搜尋配置
```bash
# 修正 config/search_config.json
{
  "search": {
    "provider": "gemini_planner_tavily",  # 改為批次查詢
    "max_results": 3
  }
}
```

### 修正 2: 重新執行效能測試
```bash
# 使用正確的批次查詢策略
python compare_phase14_phase16.py
```

### 修正 3: 實現真正的平行批次查詢

#### 方案 A: 增強 GeminiPlannerTavilyTool
```python
class EnhancedGeminiPlannerTavilyTool(BaseSearchTool):
    """增強版批次查詢工具"""
    
    def search(self, query: str, **kwargs) -> SearchResult:
        # 1. Gemini 規劃查詢框架
        queries = self.plan_queries(query)
        
        # 2. 平行執行多個查詢
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.execute_query, q) for q in queries]
            results = [f.result() for f in futures]
        
        # 3. 合併結果
        merged = self.merge_results(results)
        
        return SearchResult(...)
```

#### 方案 B: 新的平行批次查詢工具
```python
class ParallelBatchSearchTool(BaseSearchTool):
    """平行批次查詢工具"""
    
    def __init__(self):
        self.aspect_queries = {
            "foundation": "{company} 公司基本資料 成立時間 資本額",
            "core": "{company} 技術產品 服務核心",
            "vibe": "{company} 企業文化 員工評價",
            "future": "{company} 最新動態 未來發展"
        }
    
    def search(self, company: str, **kwargs) -> SearchResult:
        # 平行查詢所有面向
        queries = [q.format(company=company) for q in self.aspect_queries.values()]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(gemini_search, q): aspect 
                      for aspect, q in self.aspect_queries.items()}
            
            results = {}
            for future in as_completed(futures):
                aspect = futures[future]
                results[aspect] = future.result()
        
        return SearchResult(data=results, ...)
```

### 修正 4: Prompt 優化

#### 當前 Prompt 問題
1. **過長**: 1,856字元
2. **過於詳細**: 檢查清單、特別要求等
3. **重複要求**: 多處強調相同規則

#### 優化建議
```python
# 精簡版 Prompt（目標: < 800字元）
OPTIMIZED_PROMPT = """搜尋「{company}」的詳細資訊，返回以下四個面向的 JSON：

```json
{
  "foundation": "品牌實力與基本資料（≤500字）",
  "core": "技術產品與服務核心（≤500字）", 
  "vibe": "職場環境與企業文化（≤500字）",
  "future": "近期動態與未來展望（≤500字）"
}
```

要求：
1. 只使用搜尋到的真實資訊
2. 每個面向 ≤500字
3. 返回純 JSON，無額外文本"""
```

---

## 📈 預期改善

### 使用正確批次查詢後的預期效能

| 項目 | 當前 (gemini_fewshot) | 修正後 (gemini_planner_tavily) | 預期改善 |
|------|----------------------|-------------------------------|----------|
| **搜尋時間** | 10.49s | 6-8s | **-25% ~ -40%** |
| **API 呼叫** | 1次 | 1 + N次 | 增加 |
| **查詢品質** | 高整合度 | 高專注度 | 可能更好 |
| **可擴展性** | 低 | 高 | 大幅改善 |

### 平行批次查詢的潛在效能
```python
# 理論計算
單一查詢時間: ~2-3s
平行查詢 4個面向: ~3-4s (理論最佳)
比當前改善: ~60-70%
```

---

## 🔄 後續步驟

### 短期行動（1-2天）
1. [ ] 修正搜尋配置為 `gemini_planner_tavily`
2. [ ] 重新執行 Phase 16 效能測試
3. [ ] 更新對比報告
4. [ ] 驗證批次查詢的實際效能

### 中期行動（3-5天）
1. [ ] 實現平行批次查詢原型
2. [ ] 測試不同 Prompt 長度的效能影響
3. [ ] 建立效能基準測試
4. [ ] 優化 Prompt 結構

### 長期行動（1-2週）
1. [ ] 實現完整的平行批次查詢系統
2. [ ] 加入快取機制
3. [ ] 建立效能監控儀表板
4. [ ] 進行大規模測試（100+公司）

---

## 📚 參考文件

### 相關文件
1. [設計規範](design_spec.md) - Phase 16 設計規格
2. [測試規格](test_spec.md) - 測試工項與評估指標
3. [開發者 Prompt](developer_prompt.md) - 開發進度追蹤

### 測試結果文件
1. `phase14_test_results.json` - Phase 14 測試結果
2. `phase16_test_results.json` - Phase 16 測試結果
3. `phase14_vs_phase16_comparison_report.md` - 對比報告

### 程式碼檔案
1. `src/services/search_tools.py` - 搜尋工具實現
2. `config/search_config.json` - 搜尋配置
3. `compare_phase14_phase16.py` - 測試腳本

---

## 🎯 結論

### 主要結論
1. **Phase 16 的效能問題主要來自 Prompt 複雜度**，不是查詢策略
2. **兩個 Phase 都是「一次性批量查詢」**，設計上沒有本質差異
3. **真正的批次查詢設計意圖需要重新實現**

### 技術建議
1. **立即修正配置**，使用 `gemini_planner_tavily` 進行正確測試
2. **考慮實現平行批次查詢**，以達成真正的效能優化
3. **優化 Prompt 設計**，平衡品質與效能

### 業務影響
1. **Phase 16 提供更好的內容品質**，但需要付出效能代價
2. **批次查詢有潛在的效能優勢**，但需要正確實現
3. **Prompt 優化是關鍵**，可以大幅改善效能而不影響品質

**最終建議：優先修正配置並重新測試，然後評估是否需要實現真正的平行批次查詢。**

---

*報告生成時間: 2026-04-17*  
*分析者: Project Analyst*  
*狀態: 待執行修正行動*