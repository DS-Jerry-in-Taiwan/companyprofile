import pytest
import json
import os
import tempfile
from src.storage.factory import StorageFactory
from src.storage.sqlite_adapter import SQLiteStorage


class TestStorageIntegration:

    def test_config_to_factory_to_storage(self):
        """IT-09-01: 配置 → 工廠 → 存储完整流程"""
        config = {
            "type": "sqlite",
            "connection": "sqlite:///:memory:"
        }
        storage = StorageFactory.create(config)
        assert isinstance(storage, SQLiteStorage)

        # 验证能正常使用
        item = {
            "trace_id": "it-trace-001",
            "organ_no": "it-org-001",
            "mode": "DETAILED",
            "prompt_raw": "integration test prompt",
            "response_raw": "integration test response",
            "created_at": "2026-04-24T00:00:00"
        }
        result = storage.save_response(item)
        assert result is True

    def test_save_get_full_flow(self):
        """IT-09-02: save → get 完整流程"""
        config = {"type": "sqlite", "connection": "sqlite:///:memory:"}
        storage = StorageFactory.create(config)

        item = {
            "trace_id": "flow-trace",
            "organ_no": "flow-org",
            "mode": "BRIEF",
            "prompt_raw": "flow prompt",
            "response_raw": "flow response",
            "is_json": 1,
            "word_count": 50,
            "model": "gemini-2.0-flash",
            "created_at": "2026-04-24T12:00:00"
        }
        storage.save_response(item)

        retrieved = storage.get_response("flow-trace")
        assert retrieved is not None
        assert retrieved["trace_id"] == "flow-trace"
        assert retrieved["response_raw"] == "flow response"

    def test_data_consistency(self):
        """IT-09-03: 数据一致性 — 所有字段保存后能完全取回"""
        config = {"type": "sqlite", "connection": "sqlite:///:memory:"}
        storage = StorageFactory.create(config)

        item = {
            "trace_id": "trace-xyz",
            "organ_no": "org-consistency",
            "mode": "DETAILED",
            "prompt_raw": "original prompt text",
            "response_raw": "original response text",
            "is_json": 1,
            "word_count": 100,
            "tokens_used": 500,
            "model": "gemini-2.0-flash-lite",
            "latency_ms": 300,
            "created_at": "2026-04-24T08:30:00",
            "duration_ms": 250
        }
        storage.save_response(item)

        retrieved = storage.get_response("trace-xyz")
        for key in item:
            assert retrieved.get(key) == item[key], f"Mismatch for {key}: {retrieved.get(key)} != {item[key]}"
