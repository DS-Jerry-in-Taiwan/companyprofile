import pathlib

from src.services.risk_control_service import RiskControlService
from src.schemas.risk_models import RiskStatus


DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "tests" / "samples"


def _read(name: str) -> str:
    return (DATA_DIR / name).read_text(encoding="utf-8")


def test_obfuscated_competitor_1O4():
    svc = RiskControlService()
    txt = _read("obf_competitor_1O4.txt")
    out = svc.scan_and_decide(txt)
    # With normalizer, '1O4' should normalize to '104' and be detected
    assert out.risk_status == RiskStatus.PENDING


def test_fullwidth_linkedin():
    svc = RiskControlService()
    txt = _read("fullwidth_linkedin.txt")
    out = svc.scan_and_decide(txt)
    # fullwidth characters should be normalized to ASCII and detected
    assert out.risk_status == RiskStatus.PENDING


def test_zero_width_sensitive():
    svc = RiskControlService()
    txt = _read("zero_width_sensitive.txt")
    out = svc.scan_and_decide(txt)
    # zero-width insertion should be removed by normalizer and detected
    # depending on keyword severity this may be PENDING or REJECTED
    assert out.risk_status in (RiskStatus.PENDING, RiskStatus.REJECTED)


def test_xss_obfuscated_sanitized():
    svc = RiskControlService()
    txt = _read("xss_obfuscated.html")
    out = svc.scan_and_decide(txt)
    # sanitizer should remove script/onerror handlers
    assert "<script" not in out.body_html.lower()
    assert "onerror" not in out.body_html.lower()


def test_long_repeat_sensitive_reject():
    svc = RiskControlService()
    txt = _read("long_repeat_sensitive.txt")
    out = svc.scan_and_decide(txt)
    # repeated banned token should trigger REJECT
    assert out.risk_status == RiskStatus.REJECTED


def test_pii_like_not_flagged():
    svc = RiskControlService()
    txt = _read("pii_like.txt")
    out = svc.scan_and_decide(txt)
    # phone/email patterns should not be considered sensitive by current keywords
    assert out.risk_status in (RiskStatus.APPROVED, RiskStatus.PENDING)
    # if LinkedIn matched, it will be pending; otherwise approved


def test_mixed_en_cn_competitor_detected():
    svc = RiskControlService()
    txt = _read("mixed_en_cn_competitor.txt")
    out = svc.scan_and_decide(txt)
    # this contains exact 'LinkedIn' and '104.com.tw' so expect PENDING
    assert out.risk_status == RiskStatus.PENDING
    assert any("LinkedIn" in k or "104" in k for k in out.matched_keywords)
    assert "[COMPETITOR]" in out.body_html
