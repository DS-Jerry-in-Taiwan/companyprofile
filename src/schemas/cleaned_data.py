"""
CleanedData - 清洗後資料的 Pydantic 模型
Phase 2 - 數據檢索與前處理模組
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field, field_validator


class CleanedData(BaseModel):
    """
    清洗後的網頁內容資料模型

    Attributes:
        title: 網頁標題
        source_url: 來源網址
        content_text: 清洗後的文字內容
        token_count: 估計的 Token 數量
        scraped_at: 抓取時間
        word_count: 字數統計
    """

    title: str = Field(..., description="網頁標題", min_length=1)
    source_url: HttpUrl = Field(..., description="來源網址")
    content_text: str = Field(..., description="清洗後的文字內容", min_length=1)
    token_count: Optional[int] = Field(None, description="估計的 Token 數量")
    scraped_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="抓取時間"
    )
    word_count: Optional[int] = Field(None, description="字數統計")

    @field_validator("content_text")
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        """驗證內容不為空字符串"""
        if not v.strip():
            raise ValueError("content_text 不能為空")
        return v.strip()

    @field_validator("token_count")
    @classmethod
    def estimate_token_count(cls, v: Optional[int], info) -> int:
        """如果未提供 token_count，則估算"""
        if v is None:
            content = info.data.get("content_text", "")
            # 粗略估算：中文每字約 1 token，英文每詞約 1 token
            v = len(content)
        return v

    def truncate(self, max_tokens: int = 4000) -> "CleanedData":
        """
        截斷內容以符合 Token 限制

        Args:
            max_tokens: 最大 Token 數量

        Returns:
            截斷後的 CleanedData 實例
        """
        if self.token_count and self.token_count > max_tokens:
            # 估算需要保留的字符數
            ratio = max_tokens / self.token_count
            truncated_text = self.content_text[
                : int(len(self.content_text) * ratio * 0.9)
            ]
            return CleanedData(
                title=self.title,
                source_url=self.source_url,
                content_text=truncated_text + "\n\n[內容已截斷]",
                token_count=max_tokens,
                scraped_at=self.scraped_at,
            )
        return self

    class Config:
        """Pydantic 配置"""

        json_schema_extra = {
            "example": {
                "title": "範例公司介紹",
                "source_url": "https://example.com/about",
                "content_text": "這是一家創新的科技公司...",
                "token_count": 150,
                "word_count": 75,
            }
        }


class SearchAndExtractResult(BaseModel):
    """
    搜尋與提取的完整結果模型

    Attributes:
        query: 搜尋關鍵字
        results: 清洗後的資料列表
        total_tokens: 總 Token 數量
        success: 是否成功
        error_message: 錯誤訊息
    """

    query: str
    results: list[CleanedData] = Field(default_factory=list)
    total_tokens: int = 0
    success: bool = True
    error_message: Optional[str] = None

    def add_result(self, data: CleanedData) -> None:
        """新增結果並更新總 Token 數"""
        self.results.append(data)
        self.total_tokens = sum(r.token_count or 0 for r in self.results)
