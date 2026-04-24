"""
Pydantic Data Models for Data Retrieval & Preprocessing Module
定義數據檢索與前處理模組的資料模型
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field, field_validator
import re


class CleanedData(BaseModel):
    """清洗後的資料模型"""

    title: str = Field(..., min_length=1, max_length=500, description="資料標題")
    source_url: HttpUrl = Field(..., description="資料來源 URL")
    content_text: str = Field(..., min_length=1, description="清洗後的文字內容")
    token_count: Optional[int] = Field(None, ge=0, description="Token 數量")
    word_count: Optional[int] = Field(None, ge=0, description="字數統計")
    char_count: Optional[int] = Field(None, ge=0, description="字元數量")
    language: Optional[str] = Field(None, max_length=10, description="內容語言")
    scraped_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(), description="爬取時間"
    )
    metadata: Optional[dict] = Field(default_factory=dict, description="額外元資料")

    @field_validator("content_text")
    @classmethod
    def validate_content_text(cls, v: str) -> str:
        """驗證並清洗內容文字"""
        # 移除多餘的空白字符
        v = re.sub(r"\s+", " ", v).strip()
        if not v:
            raise ValueError("content_text cannot be empty after cleaning")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """驗證並清洗標題"""
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty")
        return v

    def calculate_counts(self) -> None:
        """計算字數、字元數和 token 數"""
        self.char_count = len(self.content_text)
        # 簡單的中英文分詞計數
        self.word_count = len(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+|\d+', self.content_text))
        # 估算 token 數（中文約 1.5 個字/Token，英文約 4 個字元/Token）
        self.token_count = self._estimate_tokens()

    def _estimate_tokens(self) -> int:
        """估算 token 數量"""
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", self.content_text))
        other_chars = self.char_count - chinese_chars if self.char_count else 0
        # 中文約 1.5 字/Token，英文約 4 字元/Token
        return int(chinese_chars / 1.5 + other_chars / 4)


class SearchResult(BaseModel):
    """搜尋結果模型"""

    url: HttpUrl = Field(..., description="搜尋結果 URL")
    title: str = Field(..., description="搜尋結果標題")
    snippet: Optional[str] = Field(None, description="搜尋結果摘要")
    position: int = Field(default=1, ge=1, description="搜尋結果位置")
    search_query: str = Field(..., description="搜尋查詢字串")
    provider: str = Field(default="unknown", description="搜尋服務提供者")

    @field_validator("snippet")
    @classmethod
    def validate_snippet(cls, v: Optional[str]) -> Optional[str]:
        """清洗摘要文字"""
        if v:
            return re.sub(r"\s+", " ", v).strip()
        return v


class ScrapedContent(BaseModel):
    """爬取內容模型"""

    url: HttpUrl = Field(..., description="爬取的 URL")
    raw_html: Optional[str] = Field(None, description="原始 HTML")
    cleaned_text: str = Field(..., description="清洗後的文字")
    title: Optional[str] = Field(None, description="頁面標題")
    meta_description: Optional[str] = Field(None, description="Meta 描述")
    success: bool = Field(default=True, description="爬取是否成功")
    error_message: Optional[str] = Field(None, description="錯誤訊息")
    status_code: Optional[int] = Field(None, description="HTTP 狀態碼")
    response_time_ms: Optional[float] = Field(None, description="回應時間（毫秒）")
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(), description="爬取時間"
    )

    @field_validator("cleaned_text")
    @classmethod
    def validate_cleaned_text(cls, v: str) -> str:
        """清洗文字內容"""
        return re.sub(r"\s+", " ", v).strip()


class PreprocessingRequest(BaseModel):
    """前處理請求模型"""

    company_name: str = Field(..., min_length=1, description="公司名稱")
    company_url: Optional[HttpUrl] = Field(None, description="公司網站 URL")
    search_query: Optional[str] = Field(None, description="自定義搜尋查詢")
    max_search_results: int = Field(
        default=5, ge=1, le=20, description="最大搜尋結果數"
    )
    require_english: bool = Field(default=False, description="是否需要英文內容")
    reference_urls: Optional[List[HttpUrl]] = Field(None, description="參考 URL 列表")


class PreprocessingResponse(BaseModel):
    """前處理回應模型"""

    request_id: str = Field(..., description="請求 ID")
    success: bool = Field(..., description="處理是否成功")
    cleaned_data: Optional[List[CleanedData]] = Field(
        None, description="清洗後的資料列表"
    )
    search_results: Optional[List[SearchResult]] = Field(
        None, description="搜尋結果列表"
    )
    error_message: Optional[str] = Field(None, description="錯誤訊息")
    processing_time_ms: Optional[float] = Field(None, description="處理時間（毫秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="處理時間戳")
