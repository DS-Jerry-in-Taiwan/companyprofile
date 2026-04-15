"""
公司簡介生成器
==============

從四面向彙整結果生成公司簡介
"""

import os
import sys
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# 取得專案根目錄
_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


class BriefLength(Enum):
    """簡介長度選項"""

    SHORT = "short"  # 100-150 字
    MEDIUM = "medium"  # 200-300 字
    LONG = "long"  # 400-500 字


@dataclass
class GeneratedBrief:
    """生成的簡介"""

    company: str
    title: str
    content: str
    length_category: str
    word_count: int
    generation_time: float


class BriefGenerator:
    """
    公司簡介生成器

    使用 LLM 從四面向資訊生成公司簡介
    """

    BRIEF_PROMPT_TEMPLATE = """你是專業的公司簡介撰寫師。請根據以下四個面向的資訊，為公司撰寫一份專業的公司簡介。

【公司名稱】
{company}

【品牌實力與基本資料 (foundation)】
{foundation}

【技術產品與服務核心 (core)】
{core}

【職場環境與企業文化 (vibe)】
{vibe}

【近期動態與未來展望 (future)】
{future}

【輸出格式 - 請嚴格遵守 JSON 格式】
{{
    "title": "簡介標題（10-20字）",
    "content": "公司簡介內容（{length_hint}）",
    "key_points": ["重點1", "重點2", "重點3"]
}}

【撰寫原則】
1. 以第三人稱撰寫
2. 突出公司特色與優勢
3. 保持專業但易讀的語調
4. {length_rule}
5. 如果某面向資訊不足，請根據可用資訊合理推斷並註明「部分資訊待確認」
"""

    LENGTH_HINTS = {
        BriefLength.SHORT: "80-120字",
        BriefLength.MEDIUM: "150-250字",
        BriefLength.LONG: "350-450字",
    }

    LENGTH_RULES = {
        BriefLength.SHORT: "極度精簡，只保留最重要資訊",
        BriefLength.MEDIUM: "平衡深度與簡潔，涵蓋主要面向",
        BriefLength.LONG: "詳細全面，盡量涵蓋所有面向",
    }

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
        summaries: Dict[str, Any],
        length: BriefLength = BriefLength.MEDIUM,
    ) -> GeneratedBrief:
        """
        生成公司簡介

        Args:
            company: 公司名稱
            summaries: 四面向彙整結果
            length: 簡介長度

        Returns:
            GeneratedBrief: 生成的簡介
        """
        start = time.time()

        # 填充各面向內容
        foundation = summaries.get("foundation", {}).get("content", "無相關資訊")
        core = summaries.get("core", {}).get("content", "無相關資訊")
        vibe = summaries.get("vibe", {}).get("content", "無相關資訊")
        future = summaries.get("future", {}).get("content", "無相關資訊")

        # 構建 Prompt
        prompt = self.BRIEF_PROMPT_TEMPLATE.format(
            company=company,
            foundation=foundation,
            core=core,
            vibe=vibe,
            future=future,
            length_hint=self.LENGTH_HINTS[length],
            length_rule=self.LENGTH_RULES[length],
        )

        # 呼叫 LLM
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                temperature=0.3,
            ),
        )

        generation_time = time.time() - start

        # 解析 JSON 回應
        import json
        import re

        raw_text = response.text if response else ""

        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw_text, re.DOTALL)

        if json_match:
            try:
                data = json.loads(json_match.group(0))
                content = data.get("content", "")
            except json.JSONDecodeError:
                content = raw_text[:500]
        else:
            content = raw_text[:500]

        # 計算字數
        word_count = len(content)

        return GeneratedBrief(
            company=company,
            title=data.get("title", f"{company} 公司簡介")
            if json_match
            else f"{company} 公司簡介",
            content=content,
            length_category=length.value,
            word_count=word_count,
            generation_time=generation_time,
        )

    def to_dict(self, brief: GeneratedBrief) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "company": brief.company,
            "title": brief.title,
            "content": brief.content,
            "length_category": brief.length_category,
            "word_count": brief.word_count,
            "generation_time": round(brief.generation_time, 2),
        }
