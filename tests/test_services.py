import sys
import os
import unittest

# Adding the src directory to the PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.serper_search import SerperSearchProvider
from src.services.web_scraper import WebScraper
from src.services.text_cleaner import TextCleaner


class TestSerperSearch(unittest.TestCase):
    """測試 SerperSearch 服務"""

    def test_search_with_mock(self):
        """測試使用 mock 搜尋"""
        search = SerperSearchProvider(api_key="dummy_value")
        results = search.search("test query", max_results=3)

        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)

        # 驗證 SearchResult 結構
        if results:
            self.assertTrue(hasattr(results[0], "url"))
            self.assertTrue(hasattr(results[0], "title"))
            self.assertTrue(hasattr(results[0], "snippet"))

    def test_search_returns_urls(self):
        """測試搜尋結果包含 URL"""
        search = SerperSearchProvider(api_key="dummy_value")
        results = search.search("Apple Inc.", max_results=2)

        for result in results:
            self.assertTrue(result.url.startswith("http"))


class TestWebScraper(unittest.TestCase):
    """測試 WebScraper 服務"""

    def test_extract_basic(self):
        """測試基本網頁抓取"""
        scraper = WebScraper(verify_ssl=False)
        content = scraper.extract("https://example.com")

        self.assertIsNotNone(content)
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)

    def test_validate_url(self):
        """測試 URL 驗證"""
        scraper = WebScraper()

        self.assertTrue(scraper.validate_url("https://example.com"))
        self.assertTrue(scraper.validate_url("http://test.org"))
        self.assertFalse(scraper.validate_url("not_a_url"))
        self.assertFalse(scraper.validate_url(""))

    def test_clean_html(self):
        """測試 HTML 清洗"""
        scraper = WebScraper()
        html = """
        <html>
            <head><style>body { color: red; }</style></head>
            <body>
                <script>console.log('test');</script>
                <article>
                    <h1>Title</h1>
                    <p>Content paragraph</p>
                </article>
            </body>
        </html>
        """
        cleaned = scraper.clean_html(html)

        self.assertNotIn("<script>", cleaned)
        self.assertNotIn("console.log", cleaned)
        self.assertIn("Title", cleaned)
        self.assertIn("Content paragraph", cleaned)


class TestTextCleaner(unittest.TestCase):
    """測試 TextCleaner 服務"""

    def test_clean_text_html_entities(self):
        """測試 HTML 實體處理"""
        cleaner = TextCleaner()
        raw_text = "Hello &nbsp; World &amp; Test"
        cleaned = cleaner.clean(raw_text)

        self.assertIn("Hello", cleaned)
        self.assertIn("World", cleaned)
        self.assertIn("Test", cleaned)
        # &nbsp; 應被轉換為空格
        self.assertNotIn("&nbsp;", cleaned)
        self.assertNotIn("&amp;", cleaned)

    def test_remove_extra_whitespace(self):
        """測試移除多餘空白"""
        cleaner = TextCleaner()
        text = "Hello    World   Test"
        cleaned = cleaner.clean(text)

        self.assertNotIn("    ", cleaned)
        self.assertEqual(cleaned, "Hello World Test")

    def test_count_tokens_estimate(self):
        """測試 token 估算"""
        cleaner = TextCleaner()
        text = "Hello World 測試文字"
        tokens = cleaner.count_tokens_estimate(text)

        self.assertIsInstance(tokens, int)
        self.assertGreater(tokens, 0)


class TestEndToEnd(unittest.TestCase):
    """端到端測試"""

    def test_search_scrape_clean_flow(self):
        """測試搜尋→抓取→清洗的完整流程 (使用 example.com)"""
        # 1. 搜尋 (使用 mock)
        search = SerperSearchProvider(api_key="dummy_value")
        results = search.search("test", max_results=1)

        self.assertGreater(len(results), 0)

        # 2. 抓取 (使用真實的 example.com)
        scraper = WebScraper(verify_ssl=False)
        content = scraper.extract("https://example.com")

        self.assertIsNotNone(content)
        self.assertGreater(len(content), 0)

        # 3. 清洗
        cleaner = TextCleaner()
        cleaned = cleaner.clean(content)

        self.assertIsNotNone(cleaned)
        self.assertGreater(len(cleaned), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
