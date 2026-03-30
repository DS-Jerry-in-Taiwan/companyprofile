# Search and Extract Pipeline - 搜尋與提取流程圖

## 概述
本文檔描述 Phase 2 數據檢索與前處理模組的完整流程。

---

## 主流程圖 (Mermaid)

```mermaid
flowchart TD
    Start([開始]) --> Input[輸入公司名稱]
    Input --> Search[呼叫 Serper Search API]
    
    Search --> CheckResult{搜尋成功?}
    
    CheckResult -->|是| FilterResults[過濾搜尋結果]
    CheckResult -->|否| UseFallback[使用 reference_url 降級]
    
    FilterResults --> CheckEmpty{結果為空?}
    CheckEmpty -->|是| UseFallback
    CheckEmpty -->|否| SelectURL[選擇前 3-5 個 URL]
    
    SelectURL --> LoopURL[遍歷 URL 列表]
    UseFallback --> SingleURL[使用單一 URL]
    
    LoopURL --> ValidateURL{URL 有效?}
    SingleURL --> ValidateURL
    
    ValidateURL -->|否| SkipURL[跳過此 URL]
    ValidateURL -->|是| ScrapeContent[使用 Trafilatura 抓取主體]
    
    SkipURL --> MoreURL{還有 URL?}
    MoreURL -->|是| LoopURL
    MoreURL -->|否| CheckData{有成功資料?}
    
    ScrapeContent --> CheckSSL{SSL 錯誤?}
    
    CheckSSL -->|是| RetrySSL[重試或跳過]
    CheckSSL -->|否| TextClean[文字清洗]
    
    RetrySSL --> CheckRetry{重試次數<3?}
    CheckRetry -->|是| ScrapeContent
    CheckRetry -->|否| SkipURL
    
    TextClean --> RemoveHTML[移除 HTML 標籤]
    RemoveHTML --> RemoveScript[移除 Script/CSS]
    RemoveScript --> RemoveNoise[移除噪音文字]
    RemoveNoise --> Normalize[統一格式]
    
    Normalize --> TokenCount[計算 Token 數]
    TokenCount --> CheckToken{Token > 4000?}
    
    CheckToken -->|是| Truncate[截斷內容]
    CheckToken -->|否| BuildResult[建立 CleanedData]
    
    Truncate --> BuildResult
    
    BuildResult --> AddToList[加入結果列表]
    AddToList --> MoreURL
    
    CheckData -->|是| MergeResult[合併所有結果]
    CheckData -->|否| ReturnError[回傳錯誤]
    
    MergeResult --> FinalCheck{總 Token < 8000?}
    FinalCheck -->|是| Success([成功回傳])
    FinalCheck -->|否| TruncateAll[截斷所有內容]
    TruncateAll --> Success
    
    ReturnError --> Fail([失敗回傳])
```

---

## 模組架構圖

```mermaid
graph TB
    subgraph "搜尋層 (Search Layer)"
        BS[BaseSearchProvider]
        SS[SerperSearch]
        MS[MockSearch]
        
        BS <|-- SS
        BS <|-- MS
    end
    
    subgraph "爬蟲層 (Scraper Layer)"
        BS2[BaseScraper]
        WS[WebScraper]
        PS[PlaywrightScraper]
        
        BS2 <|-- WS
        BS2 <|-- PS
    end
    
    subgraph "清洗層 (Cleaning Layer)"
        TC[TextCleaner]
        HTML[HTML Cleaner]
        NOISE[Noise Cleaner]
        FORMAT[Formatter]
    end
    
    subgraph "資料層 (Data Layer)"
        CD[CleanedData]
        SR[SearchAndExtractResult]
    end
    
    Search[SearchService] --> BS
    Search --> WS
    Search --> TC
    Search --> CD
    
    WS --> TC
    TC --> HTML
    TC --> NOISE
    TC --> FORMAT
    TC --> CD
    CD --> SR
```

---

## 類別關係圖

```mermaid
classDiagram
    class BaseSearchProvider {
        <<abstract>>
        +search(query, max_results) List~SearchResult~
        +handle_failure(query) void
        +filter_results(results) List~SearchResult~
    }
    
    class SerperSearch {
        -api_key: str
        -endpoint: str
        +search(query, max_results) List~SearchResult~
        +handle_failure(query) void
    }
    
    class SearchResult {
        +url: str
        +title: str
        +snippet: str
    }
    
    class BaseScraper {
        <<abstract>>
        +extract(url) str
        +handle_anti_scraping(url) str
        +validate_url(url) bool
    }
    
    class WebScraper {
        -config: ScrapingConfig
        +extract(url) str
        +handle_anti_scraping(url) str
        +clean_html(html) str
    }
    
    class CleanedData {
        +title: str
        +source_url: HttpUrl
        +content_text: str
        +token_count: int
        +truncate(max_tokens) CleanedData
    }
    
    BaseSearchProvider <|-- SerperSearch
    BaseSearchProvider ..> SearchResult
    BaseScraper <|-- WebScraper
    WebScraper ..> CleanedData
    SerperSearch ..> SearchResult
```

---

## 序列圖

```mermaid
sequenceDiagram
    participant User as 使用者
    participant SS as SearchService
    participant SP as SerperSearch
    participant WS as WebScraper
    participant TC as TextCleaner
    participant DB as 結果資料
    
    User->>SS: search_and_extract(company_name)
    
    SS->>SP: search(company_name)
    SP-->>SS: List[SearchResult]
    
    alt 搜尋成功
        SS->>SS: filter_results()
        loop For each URL
            SS->>WS: extract(url)
            alt SSL 錯誤
                WS-->>SS: Error
                SS->>WS: handle_anti_scraping(url)
            else 成功
                WS-->>SS: raw_content
            end
            
            SS->>TC: clean(raw_content)
            TC-->>SS: cleaned_text
            
            SS->>SS: truncate_if_needed()
            SS->>DB: add(CleanedData)
        end
        SS-->>User: SearchAndExtractResult
    else 搜尋失敗
        SS->>SP: handle_failure()
        SS->>SS: use_reference_url()
        SS-->>User: Error Result
    end
```

---

## 錯誤處理流程

```mermaid
flowchart LR
    E1[搜尋失敗] --> F1[使用 reference_url]
    E2[SSL 錯誤] --> F2[重試 3 次或跳過]
    E3[內容為空] --> F3[標記為失敗]
    E3 --> F4[嘗試下一個 URL]
    E4[Token 過多] --> F4[截斷至 4000 tokens]
```

---

**文件版本**: 1.0  
**最後更新**: 2026-03-27  
**作者**: @ARCH
