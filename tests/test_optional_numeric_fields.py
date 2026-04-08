# test_optional_numeric_fields.py
"""
测试可选数值字段（capital, employees, founded_year）的验证逻辑
Phase 12: 修复选填资讯导致的 POST 错误
"""

import sys
import os
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/functions"))
)
from src.functions.api_controller import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_valid_capital(client):
    """测试有效的资本额"""
    with patch(
        "src.functions.utils.web_scraper.extract_main_content",
        return_value="测试内容",
    ):
        resp = client.post(
            "/v1/company/profile/process",
            json={
                "mode": "GENERATE",
                "organNo": "123",
                "organ": "测试公司",
                "capital": 1000,  # 有效的正整数
            },
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


def test_invalid_capital_negative(client):
    """测试无效的资本额（负数）"""
    resp = client.post(
        "/v1/company/profile/process",
        json={
            "mode": "GENERATE",
            "organNo": "123",
            "organ": "测试公司",
            "capital": -100,  # 无效：负数
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "capital" in data["message"].lower()


def test_invalid_capital_zero(client):
    """测试无效的资本额（零）"""
    resp = client.post(
        "/v1/company/profile/process",
        json={
            "mode": "GENERATE",
            "organNo": "123",
            "organ": "测试公司",
            "capital": 0,  # 无效：零
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "capital" in data["message"].lower()


def test_valid_employees(client):
    """测试有效的员工人数"""
    with patch(
        "src.functions.utils.web_scraper.extract_main_content",
        return_value="测试内容",
    ):
        resp = client.post(
            "/v1/company/profile/process",
            json={
                "mode": "GENERATE",
                "organNo": "123",
                "organ": "测试公司",
                "employees": 50,  # 有效的正整数
            },
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


def test_invalid_employees_negative(client):
    """测试无效的员工人数（负数）"""
    resp = client.post(
        "/v1/company/profile/process",
        json={
            "mode": "GENERATE",
            "organNo": "123",
            "organ": "测试公司",
            "employees": -5,  # 无效：负数
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "employees" in data["message"].lower()


def test_valid_founded_year(client):
    """测试有效的成立年份"""
    with patch(
        "src.functions.utils.web_scraper.extract_main_content",
        return_value="测试内容",
    ):
        resp = client.post(
            "/v1/company/profile/process",
            json={
                "mode": "GENERATE",
                "organNo": "123",
                "organ": "测试公司",
                "founded_year": 2010,  # 有效的年份
            },
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


def test_invalid_founded_year_too_early(client):
    """测试无效的成立年份（太早）"""
    resp = client.post(
        "/v1/company/profile/process",
        json={
            "mode": "GENERATE",
            "organNo": "123",
            "organ": "测试公司",
            "founded_year": 1800,  # 无效：小于 1900
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "founded_year" in data["message"].lower()


def test_invalid_founded_year_too_late(client):
    """测试无效的成立年份（太晚）"""
    resp = client.post(
        "/v1/company/profile/process",
        json={
            "mode": "GENERATE",
            "organNo": "123",
            "organ": "测试公司",
            "founded_year": 2200,  # 无效：大于 2100
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "founded_year" in data["message"].lower()


def test_multiple_valid_optional_fields(client):
    """测试多个有效的可选字段"""
    with patch(
        "src.functions.utils.web_scraper.extract_main_content",
        return_value="测试内容",
    ):
        resp = client.post(
            "/v1/company/profile/process",
            json={
                "mode": "GENERATE",
                "organNo": "123",
                "organ": "测试公司",
                "capital": 5000,
                "employees": 100,
                "founded_year": 2015,
                "address": "台北市信义区",
                "industry": "资讯服务业",
            },
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


def test_no_optional_fields(client):
    """测试不提供任何可选字段"""
    with patch(
        "src.functions.utils.web_scraper.extract_main_content",
        return_value="测试内容",
    ):
        resp = client.post(
            "/v1/company/profile/process",
            json={
                "mode": "GENERATE",
                "organNo": "123",
                "organ": "测试公司",
            },
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


def test_optional_fields_with_word_limit(client):
    """测试可选字段与字数限制的组合"""
    with patch(
        "src.functions.utils.web_scraper.extract_main_content",
        return_value="测试内容",
    ):
        resp = client.post(
            "/v1/company/profile/process",
            json={
                "mode": "GENERATE",
                "organNo": "123",
                "organ": "测试公司",
                "capital": 2000,
                "employees": 75,
                "founded_year": 2018,
                "word_limit": 150,
            },
        )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
