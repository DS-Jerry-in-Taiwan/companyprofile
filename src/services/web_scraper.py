"""
Web Scraper Implementation
網頁爬蟲實作，支援反爬蟲處理和 SSL 錯誤處理
"""

import logging
import time
import re
from typing import Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import ssl
import urllib3
from .base_scraper import BaseScraper, ScrapingError, AntiScrapingError, ScrapingResult

logger = logging.getLogger(__name__)

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WebScraper(BaseScraper):
    """網頁爬蟲實作"""

    # 常見的 User-Agent 列表
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]

    def __init__(
        self, timeout: int = 30, verify_ssl: bool = True, max_retries: int = 3
    ):
        """
        初始化網頁爬蟲

        Args:
            timeout: 請求超時時間（秒）
            verify_ssl: 是否驗證 SSL 證書
            max_retries: 最大重試次數
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self._current_ua_index = 0

    def extract(self, url: str) -> str:
        """
        從 URL 提取主體文字

        Args:
            url: 目標網頁 URL

        Returns:
            str: 提取的文字內容
        """
        if not self.validate_url(url):
            raise ScrapingError(f"Invalid URL: {url}", url=url)

        for attempt in range(self.max_retries):
            try:
                # 取得當前 User-Agent
                user_agent = self._get_next_user_agent()

                headers = {
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }

                # 嘗試請求
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    allow_redirects=True,
                )

                # 檢查是否觸發反爬蟲機制
                if self._is_anti_scraping_response(response):
                    logger.warning(
                        f"Anti-scraping detected for {url}, attempt {attempt + 1}"
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(2**attempt)  # 指數退避
                        continue
                    else:
                        return self.handle_anti_scraping(url)

                response.raise_for_status()

                # 清洗 HTML 並提取文字
                cleaned_text = self.clean_html(response.text)

                return cleaned_text

            except ssl.SSLError as e:
                logger.error(f"SSL error for {url}: {e}")
                # SSL 驗證失敗時，禁用 SSL 驗證並重試
                self.verify_ssl = False
                continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise ScrapingError(f"Failed to scrape {url}: {str(e)}", url=url)

        raise ScrapingError(f"Max retries exceeded for {url}", url=url)

    def handle_anti_scraping(self, url: str) -> str:
        """
        處理反爬蟲機制

        Args:
            url: 目標網頁 URL

        Returns:
            str: 處理後的內容
        """
        logger.info(f"Handling anti-scraping for {url}")

        # 嘗試使用不同的策略
        strategies = [
            self._strategy_with_delay,
            self._strategy_with_referer,
            self._strategy_with_cookies,
        ]

        for strategy in strategies:
            try:
                result = strategy(url)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                continue

        raise AntiScrapingError(
            f"Unable to bypass anti-scraping for {url}",
            url=url,
            protection_type="unknown",
        )

    def clean_html(self, html_content: str) -> str:
        """
        清洗 HTML 內容，提取純文字

        Args:
            html_content: 原始 HTML 內容

        Returns:
            str: 清洗後的純文字
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # 移除不需要的標籤
        for tag in soup(
            ["script", "style", "nav", "footer", "header", "aside", "iframe"]
        ):
            tag.decompose()

        # 嘗試找到主要內容區域
        main_content = None

        # 嘗試常見的主要內容選擇器
        content_selectors = [
            "article",
            "main",
            ".content",
            ".post-content",
            ".entry-content",
            ".article-content",
            "#content",
            "#main-content",
        ]

        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # 如果找不到主要內容，使用 body
        if not main_content:
            main_content = soup.body or soup

        # 提取文字
        text = main_content.get_text(separator=" ", strip=True)

        # 清洗文字：移除多餘的空白字符
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def validate_url(self, url: str) -> bool:
        """
        驗證 URL 是否有效

        Args:
            url: 待驗證的 URL

        Returns:
            bool: URL 是否有效
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _get_next_user_agent(self) -> str:
        """取得下一個 User-Agent"""
        ua = self.USER_AGENTS[self._current_ua_index]
        self._current_ua_index = (self._current_ua_index + 1) % len(self.USER_AGENTS)
        return ua

    def _is_anti_scraping_response(self, response: requests.Response) -> bool:
        """檢查是否為反爬蟲回應"""
        # 檢查狀態碼
        if response.status_code in [403, 429, 503]:
            return True

        # 檢查常見的反爬蟲關鍵字
        anti_scraping_keywords = [
            "captcha",
            "challenge",
            "cloudflare",
            "access denied",
            "rate limit",
            "too many requests",
            "blocked",
        ]

        content_lower = response.text.lower()
        return any(keyword in content_lower for keyword in anti_scraping_keywords)

    def _strategy_with_delay(self, url: str) -> Optional[str]:
        """使用延遲策略"""
        time.sleep(5)  # 延遲 5 秒

        headers = {
            "User-Agent": self._get_next_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        response = requests.get(
            url, headers=headers, timeout=self.timeout, verify=False
        )

        if response.status_code == 200:
            return self.clean_html(response.text)

        return None

    def _strategy_with_referer(self, url: str) -> Optional[str]:
        """使用 Referer 策略"""
        headers = {
            "User-Agent": self._get_next_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        }

        response = requests.get(
            url, headers=headers, timeout=self.timeout, verify=False
        )

        if response.status_code == 200:
            return self.clean_html(response.text)

        return None

    def _strategy_with_cookies(self, url: str) -> Optional[str]:
        """使用 Cookie 策略"""
        session = requests.Session()

        # 先訪問首頁取得 Cookie
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        headers = {"User-Agent": self._get_next_user_agent()}

        # 取得首頁 Cookie
        session.get(base_url, headers=headers, timeout=self.timeout, verify=False)

        # 使用 Cookie 訪問目標頁面
        response = session.get(url, headers=headers, timeout=self.timeout, verify=False)

        if response.status_code == 200:
            return self.clean_html(response.text)

        return None

    def scrape_with_metadata(self, url: str) -> ScrapingResult:
        """
        爬取網頁並回傳包含元資料的結果

        Args:
            url: 目標網頁 URL

        Returns:
            ScrapingResult: 包含元資料的爬取結果
        """
        start_time = time.time()

        try:
            content = self.extract(url)
            response_time = (time.time() - start_time) * 1000

            # 提取標題
            soup = (
                BeautifulSoup(content, "html.parser")
                if isinstance(content, str)
                else None
            )
            title = soup.title.string if soup and soup.title else None

            return ScrapingResult(
                url=url, content=content, success=True, status_code=200
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return ScrapingResult(
                url=url,
                content="",
                success=False,
                error_message=str(e),
                status_code=getattr(e, "status_code", None),
            )
