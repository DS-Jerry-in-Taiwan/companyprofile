# test_api_controller.py
"""
針對 MVP API 進行單元測試與整合測試
"""
import sys
import os
import pytest
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/functions')))
from api_controller import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_generate_brief_success(client):
    with patch('utils.generate_brief.extract_main_content', return_value='這是測試公司的網站內容'):
        resp = client.post('/v1/company/profile/process', json={
            'mode': 'GENERATE',
            'organNo': '123',
            'organ': '測試公司',
            'companyUrl': 'https://www.example.com/test'
        })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['organNo'] == '123'
    assert data['organ'] == '測試公司'
    assert data['mode'] == 'GENERATE'
    assert 'body_html' in data
    assert 'summary' in data
    assert 'tags' in data

def test_optimize_brief_success(client):
    resp = client.post('/v1/company/profile/process', json={
        'mode': 'OPTIMIZE',
        'organNo': '456',
        'organ': '優化公司',
        'brief': '這是一段待優化的公司簡介'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['mode'] == 'OPTIMIZE'
    assert 'body_html' in data
    assert 'summary' in data
    assert 'tags' in data

def test_missing_required_field(client):
    resp = client.post('/v1/company/profile/process', json={
        'mode': 'GENERATE',
        'organ': '缺少編號公司',
        'companyUrl': 'https://www.example.com/test'
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['success'] is False
    assert data['code'] == 'INVALID_REQUEST'
    assert 'organNo' in data['message'] or 'required' in data['message']

def test_invalid_mode(client):
    resp = client.post('/v1/company/profile/process', json={
        'mode': 'INVALID',
        'organNo': '789',
        'organ': '錯誤模式公司',
        'companyUrl': 'https://www.example.com/test'
    })
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['success'] is False
    assert data['code'] == 'INVALID_REQUEST'
    assert 'mode' in data['message']


def test_html_sanitize_and_sensitive_filter(client):
    with patch('utils.optimize_brief.call_llm', return_value={
        'body_html': '<script>alert(1)</script><p>這段有情色內容</p>',
        'summary': '情色關鍵字摘要',
        'tags': ['AI', '情色']
    }):
        resp = client.post('/v1/company/profile/process', json={
            'mode': 'OPTIMIZE',
            'organNo': '999',
            'organ': '過濾公司',
            'brief': '待優化內容'
        })

    assert resp.status_code == 200
    data = resp.get_json()
    assert '<script>' not in data['body_html']
    assert '情色' not in data['body_html']
    assert '情色' not in data['summary']
    assert '情色' not in ''.join(data['tags'])
