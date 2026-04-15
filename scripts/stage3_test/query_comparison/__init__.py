"""
平行搜尋速度比較測試
====================

目標：比較 Tavily 與 Gemini Flash Lite 的平行搜尋速度
並整合彙整、簡介生成、標籤生成流程與內容評估

使用方法：
    python run.py                    # 速度測試
    python run.py --mode full        # 完整流程
    python run.py --mode brief       # 只生成簡介
    python run.py --mode compare     # 比較產出（含評估）
"""

from .parallel_runner import ParallelComparisonRunner
from .summarizer import FourAspectSummarizer
from .brief_generator import BriefGenerator, BriefLength
from .tag_generator import TagGenerator
from .evaluator import ContentEvaluator, EvaluationDimension

__version__ = "3.0.0"
__all__ = [
    "ParallelComparisonRunner",
    "FourAspectSummarizer",
    "BriefGenerator",
    "BriefLength",
    "TagGenerator",
    "ContentEvaluator",
    "EvaluationDimension",
]
