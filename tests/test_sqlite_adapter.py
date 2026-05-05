import pytest
import tempfile
import os
from src.storage.sqlite_adapter import SQLiteStorage


@pytest.fixture
def storage():
    """每个测试使用独立的临时数据库"""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    s = SQLiteStorage(f"sqlite:///{tmp.name}")
    yield s
    os.unlink(tmp.name)


class TestSQLiteStorage:

    def test_save_response(self, storage):
        """UT-05-01: 保存数据"""
        item = {
            "trace_id": "trace-001",
            "organ_no": "org-001",
            "mode": "DETAILED",
            "prompt_raw": "test prompt",
            "response_raw": "test response",
            "is_json": 0,
            "word_count": 10,
            "model": "gemini-2.0-flash",
            "created_at": "2026-04-24T00:00:00",
            "duration_ms": 100
        }
        result = storage.save_response(item)
        assert result is True

    def test_get_response_found(self, storage):
        """UT-05-02: 取回已保存的数据"""
        item = {
            "trace_id": "trace-002",
            "organ_no": "org-001",
            "mode": "BRIEF",
            "prompt_raw": "save and get",
            "response_raw": "saved response",
            "is_json": 1,
            "word_count": 20,
            "model": "gemini-2.0-flash-lite",
            "created_at": "2026-04-24T00:00:00",
            "duration_ms": 200
        }
        storage.save_response(item)
        result = storage.get_response("trace-002")
        assert result is not None
        assert result["trace_id"] == "trace-002"
        assert result["response_raw"] == "saved response"

    def test_get_response_not_found(self, storage):
        """UT-05-03: 不存在的 trace_id 返回 None"""
        result = storage.get_response("non-existent")
        assert result is None

    def test_list_by_organ(self, storage):
        """UT-05-04: 根据 organ_no 列表"""
        items = [
            {"trace_id": "t1", "organ_no": "org-A", "mode": "DETAILED", "created_at": "2026-04-24T00:00:00"},
            {"trace_id": "t2", "organ_no": "org-A", "mode": "BRIEF", "created_at": "2026-04-24T00:00:00"},
            {"trace_id": "t3", "organ_no": "org-B", "mode": "DETAILED", "created_at": "2026-04-24T00:00:00"},
        ]
        for item in items:
            storage.save_response(item)

        results = storage.list_by_organ("org-A")
        assert len(results) == 2
        assert results[0]["trace_id"] in ("t1", "t2")

    def test_data_consistency(self, storage):
        """UT-05-05: 保存後能取回相同数据"""
        item = {
            "trace_id": "trace-c",
            "organ_no": "org-C",
            "mode": "DETAILED",
            "prompt_raw": "original prompt",
            "response_raw": "original response",
            "is_json": 1,
            "word_count": 42,
            "tokens_used": 100,
            "model": "gemini-2.0-flash",
            "latency_ms": 500,
            "created_at": "2026-04-24T01:00:00",
            "duration_ms": 300
        }
        storage.save_response(item)
        result = storage.get_response("trace-c")
        for key, value in item.items():
            assert result.get(key) == value, f"字段 {key} 不一致: {result.get(key)} != {value}"
