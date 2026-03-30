import pytest
from src.schemas.llm_output import LLMOutput
from src.utils.token_manager import TokenManager


class TestLLMOutputSchema:
    def test_valid_output(self):
        output = LLMOutput(
            title="這是一個測試公司的簡介標題",
            body_html="<p>這是一段測試的公司簡介內容。</p>",
            summary="測試摘要",
        )
        assert output.title == "這是一個測試公司的簡介標題"
        assert "<p>" in output.body_html

    def test_title_too_short(self):
        with pytest.raises(Exception):
            LLMOutput(title="短", body_html="<p>內容</p>", summary="摘要")

    def test_summary_too_long(self):
        with pytest.raises(Exception):
            LLMOutput(
                title="這是一個有效的標題長度",
                body_html="<p>內容</p>",
                summary="a" * 51,
            )


class TestTokenManager:
    def setup_method(self):
        self.tm = TokenManager(max_tokens=100)

    def test_count_tokens(self):
        text = "Hello world"
        count = self.tm.count_tokens(text)
        assert count > 0

    def test_truncate_within_limit(self):
        text = "短文字"
        result = self.tm.truncate_context(text)
        assert result == text

    def test_truncate_exceeds_limit(self):
        text = " ".join(["word"] * 200)
        result = self.tm.truncate_context(text, max_token_limit=50)
        assert self.tm.count_tokens(result) <= 50
