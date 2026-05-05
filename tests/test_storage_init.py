"""
Phase A 測試：src/storage/__init__.py 全域入口

測試項目：
1. init_storage() 後 get_storage() 回傳正確 instance
2. 二次 init_storage() 不重複初始化
3. 未 init 就 get_storage() 拋 RuntimeError
4. 自訂 config 可正常 init
"""

import importlib
import pytest


class TestStorageInit:
    """測試 init_storage / get_storage 基本流程"""

    def test_init_then_get(self):
        """UT-01: init_storage 後 get_storage 回傳正確實例"""
        import src.storage
        importlib.reload(src.storage)
        from src.storage import init_storage, get_storage, is_initialized

        storage = init_storage({
            "type": "sqlite",
            "connection": "sqlite:///:memory:"
        })
        assert storage is not None
        assert get_storage() is storage
        assert is_initialized() is True

    def test_double_init_returns_same(self):
        """UT-02: 二次 init_storage 不回拋異常，回傳同一個 instance"""
        import src.storage
        importlib.reload(src.storage)
        from src.storage import init_storage

        storage = init_storage({
            "type": "sqlite",
            "connection": "sqlite:///:memory:"
        })
        result = init_storage({
            "type": "sqlite",
            "connection": "sqlite:///:memory:"
        })
        assert result is storage

    def test_custom_config_works(self):
        """UT-03: 傳入自訂 config (in-memory SQLite) 可正常 init 並寫入"""
        import src.storage
        importlib.reload(src.storage)
        from src.storage import init_storage

        storage = init_storage({
            "type": "sqlite",
            "connection": "sqlite:///:memory:"
        })
        # 驗證可以正常寫入讀取
        item = {
            "trace_id": "test-custom-config",
            "organ_no": "test-org",
            "mode": "GENERATE",
            "created_at": "2026-04-30T00:00:00",
        }
        assert storage.save_response(item) is True
        retrieved = storage.get_response("test-custom-config")
        assert retrieved is not None
        assert retrieved["trace_id"] == "test-custom-config"

    def test_get_without_init_raises(self):
        """UT-04: 未 init 直接 get_storage() 拋 RuntimeError"""
        import src.storage
        importlib.reload(src.storage)
        from src.storage import get_storage

        with pytest.raises(RuntimeError, match="Storage not initialized"):
            get_storage()

    def test_is_initialized_flag(self):
        """UT-05: is_initialized() 正確反映狀態"""
        import src.storage
        importlib.reload(src.storage)
        from src.storage import init_storage, is_initialized

        assert is_initialized() is False
        init_storage({"type": "sqlite", "connection": "sqlite:///:memory:"})
        assert is_initialized() is True
