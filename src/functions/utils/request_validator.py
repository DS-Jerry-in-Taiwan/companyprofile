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

    # Validate optional numeric fields
    capital = data.get("capital")
    if capital is not None:
        if not isinstance(capital, int) or capital <= 0:
            raise ValidationError(
                "capital must be a positive integer",
                details=[{"field": "capital", "reason": "invalid value"}],
            )

    employees = data.get("employees")
    if employees is not None:
        if not isinstance(employees, int) or employees <= 0:
            raise ValidationError(
                "employees must be a positive integer",
                details=[{"field": "employees", "reason": "invalid value"}],
            )

    founded_year = data.get("founded_year")
    if founded_year is not None:
        if (
            not isinstance(founded_year, int)
            or founded_year < 1900
            or founded_year > 2100
        ):
            raise ValidationError(
                "founded_year must be between 1900 and 2100",
                details=[{"field": "founded_year", "reason": "out of range"}],
            )

    data["optimization_mode"] = optimization_mode
    return data
