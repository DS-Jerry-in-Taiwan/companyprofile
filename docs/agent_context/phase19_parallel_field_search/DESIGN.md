# Phase19 平行字段搜尋改進方案設計文檔

## 目標
將並行查詢改為具體格式 + Google Search，並添加查詢不到的防呆機制。

## 問題分析
### Phase17 問題：
1. **未使用 Google Search 工具**：ParallelAspectSearchTool 沒有配置 `tools=[self.search_tool]`
2. **四面向格式太抽象**：foundation/core/vibe/future 格式讓 LLM 難以搜尋具體數據
3. **缺乏防呆機制**：查詢不到數據時，LLM 會編造內容

### Phase14 優點：
1. **具體字段格式**：統一編號、資本額、成立時間等具體字段
2. **能搜到真實數據**：測試顯示能搜到統一編號 42965130、資本額 5,000,000 等

## 新工具設計：ParallelFieldSearchTool

### 核心特性：
1. **具體字段平行搜尋**：平行查詢 7 個具體字段
2. **明確 Google Search 配置**：確保使用 `tools=[self.search_tool]`
3. **防呆機制**：處理查詢不到數據的情況
4. **性能優化**：保持 Phase17 的平行處理優勢

### 字段定義：
```python
FIELD_DEFINITIONS = {
    "unified_number": "統一編號（8位數字）",
    "capital": "資本額（新台幣）",
    "founded_date": "成立時間/日期",
    "address": "公司地址",
    "officer": "負責人/代表人",
    "main_services": "主要產品/服務",
    "business_items": "營業項目",
}
```

### 搜尋策略：
1. **單字段查詢**：為每個字段建立專屬查詢
2. **平行執行**：同時發送 7 個 API 請求
3. **結果合併**：合併所有字段結果
4. **防呆處理**：標記查詢不到的字段

### 防呆機制設計：
1. **查詢失敗處理**：API 錯誤時返回空值
2. **無數據標記**：搜尋不到數據時標記為 "未找到"
3. **Generate 提示**：告訴 Generate 模塊哪些字段無數據
4. **內容生成限制**：禁止編造無數據字段的內容

## 技術實現

### 類別結構：
```python
class ParallelFieldSearchTool(BaseSearchTool):
    """平行字段搜尋工具"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 配置 Gemini 客戶端
        self.client = genai.Client(api_key=api_key)
        self.search_tool = genai_types.Tool(google_search=genai_types.GoogleSearch())
    
    def search(self, query: str, **kwargs) -> SearchResult:
        # 1. 建立 7 個字段的查詢任務
        # 2. 平行執行所有查詢
        # 3. 合併結果並添加防呆標記
        # 4. 返回 SearchResult
```

### 查詢提示詞設計：
```python
FIELD_PROMPTS = {
    "unified_number": """請搜尋「{company}」的統一編號（8位數字）。
    
重要：只使用實際搜尋到的資訊。如果找不到，回覆：「未找到」。""",
    "capital": """請搜尋「{company}」的資本額（新台幣）。
    
重要：只使用實際搜尋到的資訊。如果找不到，回覆：「未找到」。""",
    # ... 其他字段
}
```

### 防呆標記格式：
```json
{
    "unified_number": "42965130",
    "capital": "5,000,000",
    "founded_date": "2018-06-05",
    "address": "高雄市鼓山區裕誠路1095號9樓",
    "officer": "紀竹祐",
    "main_services": "綠化服務, 庭園景觀工程",
    "business_items": "家畜家禽批發業, 水產品批發業...",
    "_metadata": {
        "missing_fields": [],  # 未找到的字段
        "found_fields": 7,     # 找到的字段數
        "search_time": 3.04    # 搜尋時間
    }
}
```

## 與現有方案的比較

| 特性 | Phase14 | Phase17 | Phase19 (新) |
|------|---------|---------|--------------|
| 搜尋格式 | 具體字段 | 四面向 | 具體字段 |
| Google Search | ✅ (可能) | ❌ | ✅ (明確配置) |
| 平行處理 | ❌ | ✅ | ✅ |
| 防呆機制 | ❌ | ❌ | ✅ |
| 性能 | 慢 (8.02s) | 快 (3.04s) | 快 (預計 3-4s) |
| 數據準確性 | 高 | 低 | 高 |

## 預期效果
1. **數據準確性**：能搜到像 Phase14 一樣的具體數據
2. **搜尋速度**：保持 Phase17 的平行處理速度 (2.64x 加速)
3. **防呆能力**：避免 LLM 編造無數據的內容
4. **Generate 質量**：提供 Generate 模塊更可靠的數據來源

## 測試計劃
1. **單字段搜尋測試**：驗證每個字段能否搜到數據
2. **平行性能測試**：驗證平行處理的加速效果
3. **防呆機制測試**：驗證查詢不到數據時的處理
4. **完整流程測試**：Search -> Summary -> Generate 全流程
5. **與 Phase14/17 對比**：驗證改進效果