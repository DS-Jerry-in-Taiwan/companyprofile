# token_manager.py

# Assuming a token counting library
# import token_library  # Uncomment if you have a specific library

class TokenManager:
    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens

    def count_tokens(self, text: str) -> int:
        # Placeholder token counting logic
        # Implement your actual token counting here
        return len(text.split())  # Simplified token count using words

    def truncate_context(self, text: str, max_token_limit: int = None) -> str:
        if max_token_limit is None:
            max_token_limit = self.max_tokens
        tokens = text.split()
        if len(tokens) > max_token_limit:
            return " ".join(tokens[:max_token_limit])
        return text

# Example usage with a hypothetical token limit of 100
# token_manager = TokenManager(max_tokens=100)
# truncated_text = token_manager.truncate_context("some long text")
# print(truncated_text)
