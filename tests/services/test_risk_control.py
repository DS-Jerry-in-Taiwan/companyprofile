import pathlib

from src.services.risk_control_service import RiskControlService
from src.schemas.risk_models import RiskStatus


DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "tests" / "samples"


def _read(name: str) -> str:
    return (DATA_DIR / name).read_text(encoding="utf-8")


def test_banned_reject():
    svc = RiskControlService()
    txt = _read("gambling.txt")
    out = svc.scan_and_decide(txt)
    assert out.risk_status == RiskStatus.REJECTED
    assert "博弈" in out.matched_keywords or "賭博" in out.matched_keywords


def test_competitor_mask_and_pending():
    svc = RiskControlService()
    txt = _read("competitor.txt")
    out = svc.scan_and_decide(txt)
    assert out.risk_status == RiskStatus.PENDING
    # competitor tokens should be listed
    assert any("104" in k or "LinkedIn" in k for k in out.matched_keywords)
    # masked token should appear in sanitized HTML
    assert "[COMPETITOR]" in out.body_html


def test_benign_approved():
    svc = RiskControlService()
    txt = _read("clean.txt")
    out = svc.scan_and_decide(txt)
    assert out.risk_status == RiskStatus.APPROVED
