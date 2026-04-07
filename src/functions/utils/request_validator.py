# request_validator.py
"""
Request Validator 模組
- 驗證輸入參數完整性、型別與業務邏輯
"""

from typing import Dict, Any


class ValidationError(Exception):
    def __init__(self, message: str, code: str = "INVALID_REQUEST", details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


def validate_request(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError("request body must be a JSON object")

    mode = data.get("mode")
    organ_no = data.get("organNo")
    organ = data.get("organ")

    if not organ_no or not organ:
        raise ValidationError("organNo and organ are required")

    if mode != "GENERATE":
        raise ValidationError(
            "mode must be GENERATE",
            details=[{"field": "mode", "reason": "unsupported mode"}],
        )

    word_limit = data.get("word_limit")
    if word_limit is not None:
        if not isinstance(word_limit, int) or word_limit < 50 or word_limit > 2000:
            raise ValidationError(
                "word_limit must be an integer between 50 and 2000",
                details=[{"field": "word_limit", "reason": "out of range"}],
            )

    optimization_mode = data.get("optimization_mode", "STANDARD")
    if optimization_mode not in ("STANDARD", "CONCISE", "DETAILED"):
        raise ValidationError(
            "optimization_mode must be STANDARD, CONCISE or DETAILED",
            details=[{"field": "optimization_mode", "reason": "invalid enum value"}],
        )

    data["optimization_mode"] = optimization_mode
    return data
