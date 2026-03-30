# web_scraper.py
"""
Web Scraper / Content Extractor
- 擷取網頁主內容
"""
import requests
from bs4 import BeautifulSoup

def extract_main_content(url):
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # 取主要內容區塊，這裡簡化為取 <body>
    return soup.body.get_text(separator=' ', strip=True) if soup.body else ''
