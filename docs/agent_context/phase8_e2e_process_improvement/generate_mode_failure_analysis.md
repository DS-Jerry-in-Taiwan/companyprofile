# GENERATE 模式介面失敗原因分析報告

## 問題描述

在GENERATE模式下，當傳送請求到 `/v1/company/profile/process` 端點時，系統返回錯誤：
```json
{
  "code": "INTERNAL_SERVER_ERROR",
  "message": "failed to fetch company website content",
  "request_id": "req-3cd4c476",
  "success": false
}
```

此錯誤表明在公司簡介生成流程中，網站內容擷取階段失敗。

## 根本原因分析

基於日誌檢查和程式碼分析，失敗的根本原因是網頁抓取功能在擷取目標網站內容時收到 HTTP 403 Forbidden 錯誤。

### 1. 網頁抓取功能的實現方式問題

在 `src/functions/utils/web_scraper.py` 中，內容擷取實現過於簡單：
```python
def extract_main_content(url):
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # 取主要內容區塊，這裡簡化為取 <body>
    return soup.body.get_text(separator=' ', strip=True) if soup.body else ''
```

**問題點：**
- 沒有設置適當的HTTP headers（特別是User-Agent），使得請求容易被網站識別為機器人流量並被封鎖
- 沒有處理常見的反爬蟲機制（如雲盤安全、速率限制等）
- 沒有備用的擷取策略（例如嘗試不同的User-Agent或使用代理）

### 2. 可能的網路連線問題

雖然日誌顯示是403 Forbidden而非連線逾時，但這仍可能與網路有關：
- 目標網站可能對特定地區或IP範圍有訪問限制
- 沒有重試機制來處理暫時性的網路問題
- 5秒的超時時間可能對某些網站而言過短

### 3. 目標網站的可訪問性

從日誌中可以看到失敗的URL是 `https://cn.deyeinverter.com/`：
- 這些網站可能有嚴格的反爬蟲政策
- 可能需要特定的請求頭才能正常訪問
- 某些網站可能要求執行JavaScript才能正載內容，而當前實現無法處理

### 4. 抓取邏輯中的異常處理

在 `src/functions/utils/generate_brief.py` 中：
```python
# Step 2: extract content from target URL
try:
    raw_content = extract_main_content(target_url)
except Exception as exc:
    raise ExternalServiceError('failed to fetch company website content') from exc
```

**問題點：**
- 異常訊息過於一般化，無法提供具體失敗原因（是403、404、連線逾時等）
- 沒有記錄具體的URL導致失敗，除錯困難
- 沒有嘗試備用URL（如果有多個搜尋結果的話）

### 5. 網頁搜尋結果的品質

在 `src/functions/utils/generate_brief.py` 中：
```python
# Step 1: query URL candidates (use organ name for search)
url_candidates = web_search(organ, company_url)

# Use search results if available, otherwise fallback to companyUrl or None
if url_candidates:
    target_url = url_candidates[0]  # 總是使用第一個結果
elif company_url:
    target_url = company_url
else:
    # No URL available - cannot proceed with content extraction
    raise ExternalServiceError(
        'No company URL available. Please provide a companyUrl or ensure the organ name yields search results.'
    )
```

**問題點：**
- 假設第一個搜尋結果總是最佳選擇，但實際上可能不是
- 沒有驗證搜尋結果的相關性或可訪問性
- 沒有備用機制：如果第一個結果失敗，不會嘗試其他結果

## 影響評估

1. **功能影響**：GENERATE模式完全無法運作，因為它依賴於網站內容擷取來生成公司簡介
2. **用戶體驗**：用戶收到不明確的內部伺服器錯誤，無法了解具發生問題
3. **系統可靠性**：單點失敗（依賴單一URL）使系統對網站變化高度敏感
4. **除錯困難**：錯誤訊息不具體，難以快速定位問題根源

## 建議解決方案

### 短期改進（優先級：高）

1. **改進網頁抓取headers**
   ```python
   # 在 web_scraper.py 中添加適當的headers
   headers = {
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
       'Accept-Language': 'en-US,en;q=0.5',
       'Accept-Encoding': 'gzip, deflate',
       'Connection': 'keep-alive',
   }
   resp = requests.get(url, headers=headers, timeout=10)
   ```

2. **增強異常處理和日誌**
   ```python
   # 在 generate_brief.py 中改進錯誤處理
   except Exception as exc:
       # 記錄具體失敗的URL和異常類型
       log_error(f"Failed to fetch content from {target_url}: {type(exc).__name__}: {str(exc)}", 
                 exception=exc, component="web_scraper")
       raise ExternalServiceError(
           f'failed to fetch company website content from {target_url}: {type(exc).__name__}'
       ) from exc
   ```

3. **實施備用URL機制**
   ```python
   # 在 generate_brief.py 中嘗試多個URL
   last_exception = None
   for url in url_candidates[:3]:  # 嘗試前3個結果
       try:
           raw_content = extract_main_content(url)
           break  # 成功則跳出迴圈
       except Exception as exc:
           last_exception = exc
           log_warning(f"Failed to fetch content from {url}: {str(exc)}", component="web_scraper")
           continue
   else:
       # 所有URL都失敗了
       if last_exception:
           raise ExternalServiceError(
               f'failed to fetch company website content from all attempted URLs: {str(last_exception)}'
           ) from last_exception
       else:
           raise ExternalServiceError('No URLs available for content extraction')
   ```

### 中期改進（優先級：中）

1. **添加重試機制**
   - 對於暫時性失敗（如連線逾時），實施指數退避重試
   - 對於403錯誤，可以嘗試不同的User-Agent

2. **改進內容擷取邏輯**
   - 使用更智慧的內容擷取方法（例如focus on main content areas rather than just body）
   - 考慮使用如readability-lah或類似庫來提取主要內容

3. **添加內容品質檢查**
   - 檢查擷取內容的長度和品質
   - 如果內容太短或看起來像錯誤頁面，嘗試其他來源

### 長期改進（優先級：低）

1. **整合多種內容來源**
   - 不只依賴網站刮取，也可以考慮使用公司API、結構化數據（Schema.org）或其他公開資料來源
   - 對於已知的問題網站，維護黑名單或特別處理規則

2. **實施內容快取**
   - 對成功擷取的內容進行快取，減少對同一網站的重複請求
   - 實施適當的快取失效策略

3. **添加網站特定處理**
   - 對於已知的常見網站（如主要商業資訊網站），實施特定的處理邏輯

## 實施優先級

1. **最高優先級（立即執行）**
   - 改進網頁抓取headers以避免基本的403錯誤
   - 增強異常處理以提供更具體的錯誤訊息
   - 實施備用URL機制以提高成功率

2. **高優先級（1週內執行）**
   - 添加基本的重試機制處理暫時性失敗
   - 改進日誌記錄以便更好的監控和除錯

3. **中等優先級（2-4週內執行）**
   - 實施更智慧的內容擷取和品質檢查
   - 添加內容快取機制以提高效率

4. **較低優先級（1-2個月內執行）**
   - 整合多種內容來源和網站特定處理
   - 開發更全面的內容擷取策略

## 結論

GENERATE模式的失敗主要源於網頁抓取實過於簡單，缺乏適當的反反爬蟲措施和備用機制。通過改進HTTP請求頭、增強錯誤處理、實施備用URL嘗試以及添加基本的重試機制，可以顯著提高模式的可靠性和成功率。這些改進不僅解決了當前的403錯誤問題，也使系統更能應對各種網站訪問挑戰。