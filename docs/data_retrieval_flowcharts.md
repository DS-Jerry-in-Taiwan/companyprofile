# 數據檢索與前處理模組流程圖

本文檔描述了數據檢索與前處理模組的完整流程。

## 主流程圖

```mermaid
flowchart TD
    A[搜尋開始] --> B[呼叫 Serper API]
    B --> C{過濾結果}
    C --> D{檢查是否有結果}
    
    D -->|有結果| E[提取第一個 URL]
    D -->|無結果| F[使用 reference_url]
    
    E --> G[抓取網頁內容]
    F --> G
    
    G --> H{SSL 錯誤處理}
    H -->|SSL 錯誤| I[禁用 SSL 驗證重試]
    I --> J[重新抓取]
    H -->|無錯誤| K[清洗文字]
    J --> K
    
    K --> L[計算 Token]
    L --> M[回傳 CleanedData]
    
    style A fill:#e1f5fe
    style M fill:#e8f5e9
    style D fill:#fff3e0
    style H fill:#ffebee
```

## 詳細流程圖（包含錯誤處理）

```mermaid
flowchart TD
    Start([開始]) --> Init[初始化服務]
    Init --> Validate[驗證輸入]
    
    Validate -->|有效| Search[執行搜尋]
    Validate -->|無效| Error1[回傳錯誤]
    
    Search --> CheckResult{搜尋成功?}
    CheckResult -->|成功| GetURLs[取得 URL 列表]
    CheckResult -->|失敗| Retry{重試次數 < 3?}
    
    Retry -->|是| Wait[等待指數退避]
    Wait --> Search
    Retry -->|否| Fallback[使用備用 URL]
    
    GetURLs --> PickURL[選擇第一個 URL]
    Fallback --> PickURL
    
    PickURL --> Scrape[爬取網頁]
    Scrape --> CheckSSL{SSL 錯誤?}
    
    CheckSSL -->|是| DisableSSL[禁用 SSL 驗證]
    DisableSSL --> RetryScrape[重試爬取]
    CheckSSL -->|否| CheckStatus{HTTP 狀態碼}
    
    RetryScrape --> CheckStatus
    
    CheckStatus -->|200| Extract[提取文字]
    CheckStatus -->|403/429/503| AntiScrape[處理反爬蟲]
    CheckStatus -->|其他| Error2[回傳錯誤]
    
    AntiScrape --> Strategy1[延遲策略]
    Strategy1 -->|失敗| Strategy2[Referer 策略]
    Strategy2 -->|失敗| Strategy3[Cookie 策略]
    Strategy3 -->|成功| Extract
    Strategy3 -->|失敗| Error2
    
    Extract --> Clean[清洗文字]
    Clean --> Tokenize[計算 Token]
    Tokenize --> BuildModel[建立 CleanedData]
    BuildModel --> Return[回傳結果]
    
    Error1 --> End([結束])
    Error2 --> End
    Return --> End
    
    style Start fill:#e1f5fe
    style End fill:#e1f5fe
    style Error1 fill:#ffebee
    style Error2 fill:#ffebee
    style Return fill:#e8f5e9
```

## 服務互動圖

```mermaid
sequenceDiagram
    participant Client as 客戶端
    participant Controller as API Controller
    participant Search as SerperSearchProvider
    participant Scraper as WebScraper
    participant Cleaner as TextCleaner
    participant Schema as Pydantic Models
    
    Client->>Controller: POST /v1/company/profile/process
    
    Controller->>Search: search(query, max_results)
    Search-->>Controller: List[URL]
    
    alt 有結果
        Controller->>Scraper: extract(url)
        Scraper-->>Controller: raw_html
    else 無結果
        Controller->>Controller: 使用 reference_url
    end
    
    Controller->>Cleaner: clean(text)
    Cleaner-->>Controller: cleaned_text
    
    Controller->>Schema: Create CleanedData
    Schema-->>Controller: validated_model
    
    Controller-->>Client: 200 OK + JSON
```

## 錯誤處理流程圖

```mermaid
flowchart TD
    Start([錯誤發生]) --> Classify{錯誤類型}
    
    Classify -->|搜尋錯誤| SearchErr[SearchError]
    Classify -->|爬蟲錯誤| ScrapingErr[ScrapingError]
    Classify -->|反爬蟲| AntiScrapeErr[AntiScrapingError]
    Classify -->|其他| GeneralErr[一般錯誤]
    
    SearchErr --> RetrySearch{可重試?}
    RetrySearch -->|是| ExponentialBackoff[指數退避重試]
    RetrySearch -->|否| FallbackSearch[使用備用搜尋]
    
    ScrapingErr --> CheckCode{狀態碼}
    CheckCode -->|4xx| ClientError[用戶端錯誤處理]
    CheckCode -->|5xx| ServerError[伺服器錯誤處理]
    CheckCode -->|超時| Timeout[超時處理]
    
    AntiScrapeErr --> Strategy[執行反爬蟲策略]
    Strategy -->|成功| Continue[繼續流程]
    Strategy -->|失敗| Failover[切換到備用方案]
    
    GeneralErr --> Log[記錄錯誤]
    Log --> Notify[通知監控系統]
    Notify --> ReturnError[回傳錯誤回應]
    
    ExponentialBackoff --> RetrySearch
    FallbackSearch --> ReturnError
    ClientError --> ReturnError
    ServerError --> ReturnError
    Timeout --> ReturnError
    Continue --> ReturnSuccess[回傳成功結果]
    Failover --> ReturnError
    
    style Start fill:#ffebee
    style ReturnError fill:#ffcdd2
    style ReturnSuccess fill:#c8e6c9
```

## 資料流程圖

```mermaid
flowchart LR
    subgraph Input[輸入]
        A[公司名稱]
        B[公司網站 URL]
        C[搜尋查詢]
    end
    
    subgraph Processing[處理流程]
        D[搜尋]
        E[爬取]
        F[清洗]
        G[驗證]
    end
    
    subgraph Output[輸出]
        H[CleanedData]
    end
    
    A --> D
    B --> E
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    
    style Input fill:#e3f2fd
    style Processing fill:#fff3e0
    style Output fill:#e8f5e9
```

## 模組架構圖

```mermaid
graph TB
    subgraph Services[Services Layer]
        BSP[BaseSearchProvider]
        SS[SerperSearchProvider]
        BS[BaseScraper]
        WS[WebScraper]
        TC[TextCleaner]
        TS[TextSplitter]
    end
    
    subgraph Schemas[Schemas Layer]
        CD[CleanedData]
        SR[SearchResult]
        SC[ScrapedContent]
        PR[PreprocessingRequest]
        PRs[PreprocessingResponse]
    end
    
    subgraph Utils[Utils Layer]
        WS2[web_search.py]
        WS3[web_scraper.py]
        TP[text_preprocessor.py]
    end
    
    SS --> BSP
    WS --> BS
    WS2 --> SS
    WS3 --> WS
    TP --> TC
    
    CD --> PRs
    SR --> PRs
    SC --> PRs
    
    style Services fill:#e3f2fd
    style Schemas fill:#e8f5e9
    style Utils fill:#fff3e0
```

## 使用範例

```python
from src.services import SerperSearchProvider, WebScraper, TextCleaner
from src.schemas import CleanedData, PreprocessingRequest

# 初始化服務
search_provider = SerperSearchProvider(api_key="your-api-key")
scraper = WebScraper(timeout=30, verify_ssl=True)
cleaner = TextCleaner()

# 建立請求
request = PreprocessingRequest(
    company_name="台積電",
    company_url="https://www.tsmc.com",
    max_search_results=5
)

# 執行搜尋
urls = search_provider.search(
    query=f"{request.company_name} 公司介紹",
    max_results=request.max_search_results
)

# 爬取網頁
if urls:
    content = scraper.extract(urls[0])
else:
    content = scraper.extract(str(request.company_url))

# 清洗文字
cleaned_text = cleaner.clean_for_llm(content, max_length=5000)

# 建立 CleanedData
cleaned_data = CleanedData(
    title="台積電公司介紹",
    source_url=urls[0] if urls else request.company_url,
    content_text=cleaned_text
)

# 計算 token 數
cleaned_data.calculate_counts()

print(f"Token count: {cleaned_data.token_count}")
print(f"Word count: {cleaned_data.word_count}")
```
