import tiktoken


class TokenManager:
    def __init__(self, model: str = "gpt-3.5-turbo", max_tokens: int = 4096):
        self.encoder = tiktoken.encoding_for_model(model)
        self.max_tokens = max_tokens

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def truncate_context(self, text: str, max_token_limit: int = None) -> str:
        if max_token_limit is None:
            max_token_limit = self.max_tokens
        tokens = self.encoder.encode(text)
        if len(tokens) > max_token_limit:
            truncated = tokens[:max_token_limit]
            return self.encoder.decode(truncated)
        return text
