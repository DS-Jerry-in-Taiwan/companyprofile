# core_dispatcher.py
"""
Core Logic Dispatcher
- 根據 mode 分派至對應模組
"""

from .generate_brief import generate_brief
from .request_validator import ValidationError


def dispatch_core_logic(data):
    mode = data.get("mode")
    if mode == "GENERATE":
        return generate_brief(data)
    raise ValidationError("mode must be GENERATE")
