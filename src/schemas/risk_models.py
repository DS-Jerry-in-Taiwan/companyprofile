"""Pydantic v2 models for risk control artifacts.

Defines RiskLevel, RiskStatus enums and the SanitizedContent model used across
the risk-control pipeline.
"""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Enumerates the assessed severity of content risk."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskStatus(str, Enum):
    """Enumerates final/temporary decision states for content."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SanitizedContent(BaseModel):
    """Canonical container for sanitized output and metadata.

    Fields:
    - title: sanitized title string
    - body_html: sanitized HTML body (bleach output)
    - summary: short plaintext summary for previews
    - risk_level: assessed risk severity (RiskLevel)
    - risk_status: decision marker (RiskStatus)
    - matched_keywords: list of matched sensitive/banned/competitor tokens
    """

    title: str = Field(..., description="Sanitized title")
    body_html: str = Field(..., description="Sanitized HTML body")
    summary: str = Field(..., description="Short plaintext summary for preview")
    risk_level: RiskLevel = Field(..., description="Assigned risk level")
    risk_status: RiskStatus = Field(..., description="Decision status")
    matched_keywords: List[str] = Field(
        default_factory=list, description="List of matched keywords/competitors"
    )

    # Pydantic v2 configuration
    model_config = {
        "extra": "forbid",
    }
