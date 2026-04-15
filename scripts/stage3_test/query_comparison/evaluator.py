"""
內容評估器
==========

使用 LLM 自動評估公司簡介與標籤的品質
"""

import os
import sys
import time
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

# 取得專案根目錄
_CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_FILE)))
)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


class EvaluationDimension(Enum):
    """評估維度"""

    RELEVANCE = "relevance"  # 相關性
    COMPLETENESS = "completeness"  # 完整性
    ACCURACY = "accuracy"  # 準確性
    READABILITY = "readability"  # 可讀性
    PROFESSIONALISM = "professionalism"  # 專業程度
    TAG_CONSISTENCY = "tag_consistency"  # 標籤一致性


@dataclass
class DimensionScore:
    """單一維度評分"""

    dimension: str
    score: float  # 1-10
    reason: str  # 評分理由
    max_score: float = 10.0


@dataclass
class EvaluationResult:
    """完整評估結果"""

    company: str
    provider: str
    dimensions: Dict[str, DimensionScore]
    overall_score: float  # 總分
    summary: str  # 總結
    evaluation_time: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "provider": self.provider,
            "dimensions": {
                k: {"score": v.score, "reason": v.reason, "max": v.max_score}
                for k, v in self.dimensions.items()
            },
            "overall_score": round(self.overall_score, 2),
            "summary": self.summary,
            "evaluation_time": round(self.evaluation_time, 2),
        }


class ContentEvaluator:
    """
    內容評估器

    使用 LLM 自動評估公司簡介與標籤的品質
    """

    DIMENSION_DESCRIPTIONS = {
        "relevance": "與公司的相關程度",
        "completeness": "四面向資訊覆蓋程度",
        "accuracy": "資訊的準確性與可信度",
        "readability": "文字流暢度與易讀性",
        "professionalism": "專業程度與商業價值",
        "tag_consistency": "標籤與簡介內容的一致性",
    }

    EVALUATION_PROMPT_TEMPLATE = """你是專業的內容品質評估師。請根據以下公司簡介和標籤，從多個維度進行評估。

【公司名稱】
{company}

【公司簡介】
{brief}

【標籤】
{tags}

【評估維度說明】(分數範圍 1-10)
- relevance: 簡介與公司的相關程度
- completeness: 四面向（foundation/core/vibe/future）資訊覆蓋程度
- accuracy: 資訊的準確性與可信度
- readability: 文字流暢度與易讀性
- professionalism: 專業程度與商業價值
- tag_consistency: 標籤與簡介內容的一致性

【輸出格式 - 只需要回覆這個 JSON，不要有其他文字】
{{
    "relevance": 8,
    "completeness": 7,
    "accuracy": 8,
    "readability": 9,
    "professionalism": 8,
    "tag_consistency": 7,
    "overall_score": 8.0,
    "summary": "一句話總結"
}}

請只回覆這個 JSON，不要有其他文字："""

    def __init__(self, model: str = "gemini-2.0-flash-lite"):
        from google import genai
        from google.genai import types

        self.model = model

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self._types = types

    def evaluate(
        self,
        company: str,
        brief: str,
        tags: List[str],
        provider: str = "unknown",
    ) -> EvaluationResult:
        """
        評估簡介與標籤

        Args:
            company: 公司名稱
            brief: 公司簡介
            tags: 標籤列表
            provider: 來源 provider

        Returns:
            EvaluationResult: 評估結果
        """
        start = time.time()

        # 構建 Prompt
        prompt = self.EVALUATION_PROMPT_TEMPLATE.format(
            company=company,
            brief=brief,
            tags=", ".join(tags) if tags else "無",
        )

        # 呼叫 LLM
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                temperature=0.1,
            ),
        )

        evaluation_time = time.time() - start

        # 解析 JSON 回應
        import json
        import re

        raw_text = response.text if response else ""

        # 移除 markdown code block 標籤
        cleaned = re.sub(r"```json\s*", "", raw_text)
        cleaned = re.sub(r"```\s*", "", cleaned)
        cleaned = cleaned.strip()

        # 嘗試直接解析
        data = None
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # 嘗試找第一個 { 到最後一個 }
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

        # 建構維度評分
        dimensions = {}
        if data:
            for dim in EvaluationDimension:
                dim_name = dim.value
                score_val = data.get(dim_name, 0)
                if isinstance(score_val, dict):
                    dimensions[dim_name] = DimensionScore(
                        dimension=dim_name,
                        score=score_val.get("score", 0),
                        reason=score_val.get("reason", score_val.get("說明", "")),
                    )
                else:
                    dimensions[dim_name] = DimensionScore(
                        dimension=dim_name,
                        score=score_val if isinstance(score_val, (int, float)) else 0,
                        reason=data.get(f"{dim_name}_reason", ""),
                    )
            overall = data.get(
                "overall_score",
                sum(d.score for d in dimensions.values()) / len(dimensions)
                if dimensions
                else 0,
            )
            summary = data.get("summary", "")
        else:
            for dim in EvaluationDimension:
                dimensions[dim.value] = DimensionScore(
                    dimension=dim.value,
                    score=0,
                    reason="評估解析失敗",
                )
            overall = 0
            summary = f"無法解析評估結果。原始回應: {cleaned[:200]}"

        return EvaluationResult(
            company=company,
            provider=provider,
            dimensions=dimensions,
            overall_score=overall,
            summary=summary,
            evaluation_time=evaluation_time,
        )

    def compare(
        self,
        company: str,
        tavily_brief: str,
        tavily_tags: List[str],
        gemini_brief: str,
        gemini_tags: List[str],
    ) -> Dict[str, Any]:
        """
        比較兩個 provider 的產出

        Args:
            company: 公司名稱
            tavily_brief: Tavily 簡介
            tavily_tags: Tavily 標籤
            gemini_brief: Gemini 簡介
            gemini_tags: Gemini 標籤

        Returns:
            Dict: 比較結果
        """
        print(f"\n📊 內容評估中...")

        # 分別評估
        tavily_result = self.evaluate(company, tavily_brief, tavily_tags, "tavily")
        gemini_result = self.evaluate(
            company, gemini_brief, gemini_tags, "gemini_flash"
        )

        # 比較各維度
        dimension_comparison = {}
        tavily_wins = 0
        gemini_wins = 0

        for dim in EvaluationDimension:
            dim_name = dim.value
            tavily_score = tavily_result.dimensions.get(
                dim_name, DimensionScore(dim_name, 0, "")
            ).score
            gemini_score = gemini_result.dimensions.get(
                dim_name, DimensionScore(dim_name, 0, "")
            ).score

            winner = "tavily" if tavily_score > gemini_score else "gemini_flash"
            if tavily_score > gemini_score:
                tavily_wins += 1
            elif gemini_score > tavily_score:
                gemini_wins += 1

            dimension_comparison[dim_name] = {
                "tavily": round(tavily_score, 1),
                "gemini_flash": round(gemini_score, 1),
                "winner": winner,
                "diff": round(abs(tavily_score - gemini_score), 1),
            }

        return {
            "company": company,
            "tavily": tavily_result.to_dict(),
            "gemini_flash": gemini_result.to_dict(),
            "dimension_comparison": dimension_comparison,
            "winner_counts": {
                "tavily": tavily_wins,
                "gemini_flash": gemini_wins,
            },
            "overall_winner": "tavily"
            if tavily_result.overall_score > gemini_result.overall_score
            else "gemini_flash",
        }

    def generate_radar_data(self, evaluation: EvaluationResult) -> Dict[str, Any]:
        """
        生成雷達圖資料

        Args:
            evaluation: 評估結果

        Returns:
            Dict: 雷達圖格式的資料
        """
        labels = []
        values = []

        for dim in EvaluationDimension:
            dim_name = dim.value
            if dim_name in evaluation.dimensions:
                labels.append(self.DIMENSION_DESCRIPTIONS.get(dim_name, dim_name))
                values.append(evaluation.dimensions[dim_name].score)

        return {
            "labels": labels,
            "values": values,
            "max": 10,
        }
