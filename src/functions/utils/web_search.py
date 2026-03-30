# web_search.py
"""
Web Search Service (Stub)
- 實際可串接 Serper.dev 或其他搜尋 API
"""
def web_search(company_name, company_url=None):
    # TODO: 串接搜尋 API；MVP 階段先回傳入參 URL 以避免阻塞流程
    if company_url:
        return [company_url]
    return [f"https://www.example.com/{company_name}"]
