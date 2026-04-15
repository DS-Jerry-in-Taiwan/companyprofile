"""
標籤生成器
==========

從公司簡介生成相關標籤
"""

import os
import sys
import time
from typing import Dict, Any, List
from dataclasses import dataclass

# 取得專案根目錄
_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


@dataclass
class GeneratedTags:
    """生成的標籤"""

    company: str
    tags: List[str]
    categories: Dict[str, List[str]]
    generation_time: float


class TagGenerator:
    """
    標籤生成器

    從公司簡介和四面向資訊自動生成標籤
    """

    TAG_PROMPT_TEMPLATE = """你是專業的內容標籤專家。請根據以下資訊，為公司生成相關標籤。

【公司名稱】
{company}

【公司簡介】
{brief}

【四面向資訊】
{foundation_info}
{core_info}
{vibe_info}
{future_info}

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "tags": ["標籤1", "標籤2", "標籤3", "標籤4", "標籤5", "標籤6", "標籤7", "標籤8"],
    "categories": {{
        "industry": ["產業標籤1", "產業標籤2"],
        "feature": ["特色標籤1", "特色標籤2"],
        "culture": ["文化標籤1", "文化標籤2"],
        "scale": ["規模標籤"]
    }}
}}

【標籤原則】
1. 標籤數量：8-12 個
2. 分類包含：industry（產業）、feature（特色）、culture（文化）、scale（規模）
3. 標籤要精準、具辨識度
4. 優先使用熱門標籤，便於搜尋
5. 每個面向至少產生 1-2 個標籤
"""

    def __init__(self, model: str = "gemini-2.0-flash-lite"):
        from google import genai
        from google.genai import types

        self.model = model

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self._types = types

    def generate(
        self,
        company: str,
        brief: str,
        summaries: Dict[str, Any],
    ) -> GeneratedTags:
        """
        生成標籤

        Args:
            company: 公司名稱
            brief: 公司簡介
            summaries: 四面向彙整結果

        Returns:
            GeneratedTags: 生成的標籤
        """
        start = time.time()

        # 提取各面向資訊（取前 200 字）
        foundation_info = summaries.get("foundation", {}).get("content", "無")[:200]
        core_info = summaries.get("core", {}).get("content", "無")[:200]
        vibe_info = summaries.get("vibe", {}).get("content", "無")[:200]
        future_info = summaries.get("future", {}).get("content", "無")[:200]

        # 構建 Prompt
        prompt = self.TAG_PROMPT_TEMPLATE.format(
            company=company,
            brief=brief[:300],
            foundation_info=foundation_info,
            core_info=core_info,
            vibe_info=vibe_info,
            future_info=future_info,
        )

        # 呼叫 LLM
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                temperature=0.2,
            ),
        )

        generation_time = time.time() - start

        # 解析 JSON 回應
        import json
        import re

        raw_text = response.text if response else ""

        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw_text, re.DOTALL)

        tags = []
        categories = {
            "industry": [],
            "feature": [],
            "culture": [],
            "scale": [],
        }

        if json_match:
            try:
                data = json.loads(json_match.group(0))
                tags = data.get("tags", [])
                categories = data.get("categories", categories)
            except json.JSONDecodeError:
                tags = ["待確認"]
        else:
            # 回退：從簡介中提取關鍵詞
            tags = self._extract_keywords(brief)

        return GeneratedTags(
            company=company,
            tags=tags,
            categories=categories,
            generation_time=generation_time,
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """從文字中提取關鍵詞（簡單 fallback）"""
        import re

        # 簡單的關鍵詞模式
        patterns = [
            r"[A-Za-z0-9]{2,}(?:公司|企業|集團|科技|實業)",
            r"(?:半導體|AI|人工智慧|軟體|硬體|電子|製造|服務|金融|電商)",
            r"(?:上市|上櫃|興櫃|新創|中小型)",
        ]

        keywords = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches[:2])

        return list(set(keywords))[:8] if keywords else ["待確認"]

    def to_dict(self, tags: GeneratedTags) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "company": tags.company,
            "tags": tags.tags,
            "categories": tags.categories,
            "generation_time": round(tags.generation_time, 2),
        }
