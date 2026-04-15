"""
四面向彙整器
============

將搜尋結果按四個面向（foundation/core/vibe/future）彙整
"""

import os
import sys
from typing import Dict, Any, List
from dataclasses import dataclass

# 取得專案根目錄
_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)


@dataclass
class AspectSummary:
    """單一面向彙整結果"""

    aspect: str
    description: str
    combined_content: str
    source_queries: int
    total_characters: int


class FourAspectSummarizer:
    """
    四面向彙整器

    將多個查詢結果彙整成四個面向的摘要
    """

    ASPECT_DESCRIPTIONS = {
        "foundation": "品牌實力與基本資料",
        "core": "技術產品與服務核心",
        "vibe": "職場環境與企業文化",
        "future": "近期動態與未來展望",
    }

    def __init__(self):
        pass

    def summarize(
        self, query_results: List[Dict[str, Any]]
    ) -> Dict[str, AspectSummary]:
        """
        彙整查詢結果為四個面向

        Args:
            query_results: 查詢結果列表

        Returns:
            Dict[str, AspectSummary]: 四個面向的彙整結果
        """
        # 按面向分組
        grouped = {aspect: [] for aspect in self.ASPECT_DESCRIPTIONS.keys()}

        for result in query_results:
            aspect = result.get("aspect", "")
            if aspect in grouped:
                grouped[aspect].append(result)

        # 彙整每個面向
        summaries = {}

        for aspect, queries in grouped.items():
            if not queries:
                continue

            # 合併所有回答
            combined_parts = []
            total_chars = 0

            for q in queries:
                if q.get("success") and q.get("answer"):
                    answer = q["answer"].strip()
                    if answer:
                        combined_parts.append(answer)
                        total_chars += len(answer)

            combined_content = "\n\n".join(combined_parts)

            summaries[aspect] = AspectSummary(
                aspect=aspect,
                description=self.ASPECT_DESCRIPTIONS.get(aspect, ""),
                combined_content=combined_content,
                source_queries=len([q for q in queries if q.get("success")]),
                total_characters=total_chars,
            )

        return summaries

    def to_dict(self, summaries: Dict[str, AspectSummary]) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {}
        for aspect, summary in summaries.items():
            result[aspect] = {
                "description": summary.description,
                "content": summary.combined_content,
                "source_queries": summary.source_queries,
                "total_characters": summary.total_characters,
            }
        return result
