"""
Services Package
數據檢索與前處理模組的服務類別
"""

from .base_search_provider import BaseSearchProvider, SearchError
from .base_scraper import BaseScraper, ScrapingError, AntiScrapingError, ScrapingResult
from .serper_search import SerperSearchProvider
from .web_scraper import WebScraper
from .text_cleaner import TextCleaner, TextSplitter
from .data_retrieval_service import (
    DataRetrievalService,
    create_data_retrieval_service,
    process_company_data_retrieval,
)

__all__ = [
    "BaseSearchProvider",
    "SearchError",
    "BaseScraper",
    "ScrapingError",
    "AntiScrapingError",
    "ScrapingResult",
    "SerperSearchProvider",
    "WebScraper",
    "TextCleaner",
    "TextSplitter",
    "DataRetrievalService",
    "create_data_retrieval_service",
    "process_company_data_retrieval",
]
