"""
Gemini Flash Lite 搜尋提供者
============================

使用主流程的 SearchResult dataclass
"""

# 路徑已在 providers/__init__.py 中設定
import os
import sys
import time
import asyncio
from typing import Dict, Any

from src.services.search_tools import SearchResult
from .base_provider import BaseSearchProvider


class GeminiFlashSearchProvider(BaseSearchProvider):
    """Gemini Flash Lite 搜尋提供者"""

    @property
    def provider_name(self) -> str:
        return "gemini_flash"

    def __init__(self, model: str = "gemini-2.0-flash-lite"):
        from google import genai
        from google.genai import types

        self.model = model

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self._types = types
        self.search_tool = types.Tool(google_search=types.GoogleSearch())

    async def search(self, query: str) -> SearchResult:
        """執行單一搜尋"""
        start = time.time()

        # 構建 Prompt：要求搜尋並回傳簡短答案
        prompt = f"""請搜尋以下資訊並用一段話回答：

{query}

請用繁體中文回答，盡量簡潔明瞭。"""

        try:
            loop = asyncio.get_event_loop()

            def sync_call():
                return self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self._types.GenerateContentConfig(
                        tools=[self.search_tool],
                        temperature=0.2,
                    ),
                )

            response = await loop.run_in_executor(None, sync_call)

            elapsed = time.time() - start
            answer = response.text if response else ""

            return SearchResult(
                success=True,
                tool_type=self.provider_name,
                elapsed_time=elapsed,
                api_calls=1,
                data={},
                raw_answer=answer,
                answer_length=len(answer),
            )
        except Exception as e:
            return SearchResult(
                success=False,
                tool_type=self.provider_name,
                elapsed_time=time.time() - start,
                api_calls=1,
                data={},
                raw_answer="",
                answer_length=0,
            )


# 全域實例
_gemini_provider = None


def get_gemini_provider() -> GeminiFlashSearchProvider:
    """取得 Gemini Flash 提供者實例（單例）"""
    global _gemini_provider
    if _gemini_provider is None:
        _gemini_provider = GeminiFlashSearchProvider()
    return _gemini_provider


async def gemini_flash_search(query: str) -> SearchResult:
    """便捷函式：執行 Gemini Flash Lite 搜尋"""
    provider = get_gemini_provider()
    return await provider.search(query)
