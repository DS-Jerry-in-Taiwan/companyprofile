"""Risk control service: normalization, scanning, masking and decisioning.

Exposes RiskControlService.scan_and_decide which returns a
SanitizedContent Pydantic model.
"""

from __future__ import annotations

from typing import List

from pydantic import ValidationError

from src.schemas.risk_models import SanitizedContent, RiskLevel, RiskStatus
from src.services.risk_scanner import DEFAULT_SCANNER
from src.services.html_sanitizer import sanitize as sanitize_html
from src.utils.token_manager import TokenManager


class RiskControlService:
    """Main orchestration for scanning and making content decisions."""

    def __init__(self) -> None:
        self.scanner = DEFAULT_SCANNER
        self.token_mgr = TokenManager()

        # define tokens considered severe/banned -> REJECT
        self._banned_tokens = {
            "博弈",
            "賭博",
            "詐騙",
            "色情",
            "毒品",
            "恐怖主義",
            "詐欺",
            "洗錢",
        }

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        return text.strip()

    def _mask_competitors(self, text: str, competitors: List[str]) -> str:
        masked = text
        for comp in competitors:
            if not comp:
                continue
            masked = masked.replace(comp, "[COMPETITOR]")
        return masked

    def scan_and_decide(self, raw_text: str) -> SanitizedContent:
        """Run full pipeline: normalize, scan, mask, sanitize, and decide.

        Returns a SanitizedContent model.
        """
        title = self._normalize(raw_text[:60])
        normalized = self._normalize(raw_text)

        matched_sensitive, matched_competitor = self.scanner.scan_text(normalized)

        # Mask competitors in the HTML/body and sanitize
        body_masked = self._mask_competitors(normalized, matched_competitor)
        body_html = sanitize_html(body_masked)

        # decide risk
        risk_level = RiskLevel.LOW
        risk_status = RiskStatus.APPROVED

        matched_keywords = []
        if matched_sensitive:
            matched_keywords.extend(matched_sensitive)
            # if any banned tokens appear -> REJECT
            if any(tok in self._banned_tokens for tok in matched_sensitive):
                risk_level = RiskLevel.HIGH
                risk_status = RiskStatus.REJECTED
            else:
                risk_level = RiskLevel.MEDIUM
                risk_status = RiskStatus.PENDING

        if matched_competitor and risk_status != RiskStatus.REJECTED:
            # competitor presence downgrades to PENDING if not already rejected
            matched_keywords.extend(matched_competitor)
            if risk_status != RiskStatus.PENDING:
                risk_level = RiskLevel.LOW
                risk_status = RiskStatus.PENDING

        # summary: simple plaintext excerpt limited by tokens
        summary = normalized[:200]
        # try to respect token truncation (best-effort)
        try:
            summary = self.token_mgr.truncate_context(summary, max_token_limit=90)
        except Exception:
            # fallback to raw slicing
            summary = summary

        # Build sanitized content model
        try:
            sanitized = SanitizedContent(
                title=title or "",
                body_html=body_html or "",
                summary=summary or "",
                risk_level=risk_level,
                risk_status=risk_status,
                matched_keywords=matched_keywords,
            )
        except ValidationError as exc:
            raise

        return sanitized
