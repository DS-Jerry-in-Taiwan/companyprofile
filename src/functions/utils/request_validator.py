# request_validator.py
"""
Request Validator 模組
- 驗證輸入參數完整性、型別與業務邏輯
"""

from typing import Dict, Any

# ErrorCode constants (string directly)
ErrorCodes = {
    "API_001": "API_001",  # Invalid request format
    "API_002": "API_002",  # Missing required field
    "API_003": "API_003",  # Invalid field value
}


class ValidationError(Exception):
    def __init__(self, message: str, code: str = "API_002", details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


def validate_request(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError("request body must be a JSON object", code=ErrorCodes["API_001"])

    mode = data.get("mode")
    organ_no = data.get("organNo")
    organ = data.get("organ")

    if not organ_no or not organ:
        raise ValidationError("organNo and organ are required", code=ErrorCodes["API_002"])

    if mode != "GENERATE":
        raise ValidationError(
            "mode must be GENERATE",
            code=ErrorCodes["API_003"],
            details=[{"field": "mode", "reason": "unsupported mode"}],
        )

    optimization_mode = data.get("optimization_mode", "STANDARD")
    if optimization_mode not in ("STANDARD", "CONCISE", "DETAILED"):
        raise ValidationError(
            "optimization_mode must be STANDARD, CONCISE or DETAILED",
            code=ErrorCodes["API_003"],
            details=[{"field": "optimization_mode", "reason": "invalid enum value"}],
        )

    # Phase 17: 搜尋策略
    search_strategy = data.get("search_strategy", "complete")
    if search_strategy not in ("fast", "basic", "complete", "deep"):
        raise ValidationError(
            "search_strategy must be fast, basic, complete or deep",
            code=ErrorCodes["API_003"],
            details=[{"field": "search_strategy", "reason": "invalid enum value"}],
        )

    data["optimization_mode"] = optimization_mode
    return data
