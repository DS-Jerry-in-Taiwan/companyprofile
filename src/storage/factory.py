from .base import StorageInterface


class StorageFactory:
    """统一入口，通过配置创建适配器"""

    @staticmethod
    def create(config: dict) -> StorageInterface:
        storage_type = config.get("type", "sqlite")

        if storage_type == "sqlite":
            from .sqlite_adapter import SQLiteStorage
            return SQLiteStorage(config.get("connection"))

        elif storage_type == "dynamodb":
            from .dynamodb_adapter import DynamoDBStorage
            return DynamoDBStorage(
                llm_responses_table=config.get("llm_responses_table"),
                error_logs_table=config.get("error_logs_table"),
                region=config.get("region", "ap-northeast-1"),
            )

        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
