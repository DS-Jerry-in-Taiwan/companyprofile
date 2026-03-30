import requests
from bs4 import BeautifulSoup
import ssl
import urllib3
import time
from random import uniform
import logging

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def scrape_website(url):
    """
    抓取網頁內容並提取主體文字

    Args:
        url: 目標網頁 URL

    Returns:
        str: 提取的文字內容
    """
    try:
        # 設定 User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # 嘗試使用 requests 抓取
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
            verify=False,  # 禁用 SSL 驗證
            allow_redirects=True,
        )

        response.raise_for_status()

        # 使用 BeautifulSoup 提取文字
        soup = BeautifulSoup(response.text, "html.parser")

        # 移除不需要的標籤
        for tag in soup(
            ["script", "style", "nav", "footer", "header", "aside", "iframe"]
        ):
            tag.decompose()

        # 提取文字
        text = soup.get_text(separator=" ", strip=True)

        return text

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None


class Scraper:
    """網頁爬蟲類別，支援重試機制"""

    def __init__(self, retry_attempts=3):
        """
        初始化爬蟲

        Args:
            retry_attempts: 重試次數
        """
        self.retry_attempts = retry_attempts

    def scrape(self, url):
        """
        抓取網頁內容

        Args:
            url: 目標網頁 URL

        Returns:
            str: 提取的文字內容，失敗時返回 None
        """
        for attempt in range(self.retry_attempts):
            content = scrape_website(url)
            if content:
                return content
            sleep_time = uniform(1, 3)
            time.sleep(sleep_time)
        return None
