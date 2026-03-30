"""
Base Scraper Abstract Class
定義網頁爬蟲的抽象介面，支援不同爬蟲實作與反爬蟲處理
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class ScrapingResult:
    """爬蟲結果資料類別"""

    url: str
    content: str
    success: bool
    error_message: Optional[str] = None
    status_code: Optional[int] = None


class BaseScraper(ABC):
    """網頁爬蟲的抽象基礎類別"""

    @abstractmethod
    def extract(self, url: str) -> str:
        """
        從 URL 提取主體文字

        Args:
            url: 目標網頁 URL

        Returns:
            str: 提取的文字內容

        Raises:
            ScrapingError: 爬取失敗時拋出
        """
        pass

    @abstractmethod
    def handle_anti_scraping(self, url: str) -> str:
        """
        處理反爬蟲機制

        Args:
            url: 目標網頁 URL

        Returns:
            str: 處理後的內容

        Raises:
            AntiScrapingError: 反爬蟲處理失敗時拋出
        """
        pass

    @abstractmethod
    def clean_html(self, html_content: str) -> str:
        """
        清洗 HTML 內容，提取純文字

        Args:
            html_content: 原始 HTML 內容

        Returns:
            str: 清洗後的純文字
        """
        pass

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """
        驗證 URL 是否有效

        Args:
            url: 待驗證的 URL

        Returns:
            bool: URL 是否有效
        """
        pass


class ScrapingError(Exception):
    """爬蟲錯誤"""

    def __init__(self, message: str, url: str = "", status_code: Optional[int] = None):
        self.message = message
        self.url = url
        self.status_code = status_code
        super().__init__(self.message)


class AntiScrapingError(ScrapingError):
    """反爬蟲錯誤"""

    def __init__(self, message: str, url: str = "", protection_type: str = ""):
        self.protection_type = protection_type
        super().__init__(message, url)
