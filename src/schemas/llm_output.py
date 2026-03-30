from pydantic import BaseModel, Field
from typing import Optional


class LLMOutput(BaseModel):
    """LLM 輸出結構化模型"""

    title: str = Field(..., min_length=10, max_length=50, description="公司簡介標題")
    body_html: str = Field(..., description="公司簡介正文（HTML 格式）")
    summary: str = Field(..., max_length=50, description="一句話摘要")
