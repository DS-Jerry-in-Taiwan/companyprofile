from .base import StorageInterface


class StorageFactory:
    """统一入口，通过配置创建适配器"""

    @staticmethod
    def create(config: dict) -> StorageInterface:
        storage_type = config.get("type", "sqlite")

        if storage_type == "sqlite":
            from .sqlite_adapter import SQLiteStorage
            return SQLiteStorage(config.get("connection"))

        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
