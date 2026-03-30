"""Centralized error types and formatting helpers."""


class ExternalServiceError(Exception):
    def __init__(self, message: str, code: str = 'EXTERNAL_SERVICE_ERROR'):
        super().__init__(message)
        self.code = code
        self.message = message


class LLMServiceError(Exception):
    def __init__(self, message: str, code: str = 'LLM_FAILED'):
        super().__init__(message)
        self.code = code
        self.message = message
