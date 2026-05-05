"""
Phase B 測試：DynamoDB Adapter + Factory 擴充

測試項目：
1. Factory 建立 DynamoDBStorage
2. save_response → get_response 流程
3. save_error → list_errors 流程
4. list_by_organ GSI 查詢
5. 缺少 trace_id 不 crash
6. Factory unknown type 拋 ValueError
7. 既有 SQLite 測試不受影響
"""

from unittest.mock import MagicMock, patch
import pytest
from src.storage.factory import StorageFactory
from src.storage.dynamodb_adapter import DynamoDBStorage


class TestFactoryDynamoDB:
    """Factory 建立 DynamoDBStorage"""

    def test_factory_creates_dynamodb(self):
        """UT-B1: Factory 建立 DynamoDBStorage"""
        storage = StorageFactory.create({
            "type": "dynamodb",
            "region": "ap-northeast-1",
            "llm_responses_table": "test-llm-responses",
            "error_logs_table": "test-error-logs",
        })
        assert isinstance(storage, DynamoDBStorage)

    def test_factory_unknown_type(self):
        """UT-B2: Factory unknown type 拋 ValueError"""
        with pytest.raises(ValueError, match="Unknown storage type"):
            StorageFactory.create({"type": "postgres"})

    def test_factory_sqlite_still_works(self):
        """UT-B3: 既有 SQLite factory 不受影響"""
        storage = StorageFactory.create({
            "type": "sqlite",
            "connection": "sqlite:///:memory:"
        })
        from src.storage.sqlite_adapter import SQLiteStorage
        assert isinstance(storage, SQLiteStorage)
        # 驗證可寫入
        storage.save_response({
            "trace_id": "sqlite-test",
            "organ_no": "org",
            "mode": "TEST",
            "created_at": "2026-04-30T00:00:00",
        })
        retrieved = storage.get_response("sqlite-test")
        assert retrieved["trace_id"] == "sqlite-test"


class TestDynamoDBStorage:
    """DynamoDBStorage 基本流程測試（mock boto3）"""

    @pytest.fixture
    def mock_table(self):
        """建立 mock DynamoDB table"""
        table = MagicMock()
        # put_item 回傳成功
        table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        return table

    @pytest.fixture
    def storage(self, mock_table):
        """建立 DynamoDBStorage 並注入 mock table"""
        with patch.object(DynamoDBStorage, 'responses_table', mock_table), \
             patch.object(DynamoDBStorage, 'errors_table', mock_table):
            storage = DynamoDBStorage(
                llm_responses_table="test-llm-responses",
                error_logs_table="test-error-logs",
                region="ap-northeast-1",
            )
            yield storage

    def test_save_response(self, storage, mock_table):
        """UT-B4: save_response 正常寫入"""
        item = {
            "trace_id": "trace-001",
            "organ_no": "org-001",
            "mode": "GENERATE",
            "created_at": "2026-04-30T00:00:00",
        }
        result = storage.save_response(item)
        assert result is True
        mock_table.put_item.assert_called_once_with(Item=item)

    def test_save_response_without_trace_id(self, storage, mock_table):
        """UT-B5: 缺少 trace_id 回傳 False，不 crash"""
        result = storage.save_response({"organ_no": "org-001"})
        assert result is False
        mock_table.put_item.assert_not_called()

    def test_save_response_adds_created_at(self, storage, mock_table):
        """UT-B6: 沒有 created_at 時自動補上"""
        item = {"trace_id": "trace-002", "organ_no": "org-001"}
        result = storage.save_response(item)
        assert result is True
        # 驗證有補上 created_at
        call_args = mock_table.put_item.call_args[1]["Item"]
        assert "created_at" in call_args
        assert call_args["trace_id"] == "trace-002"

    def test_get_response_with_created_at(self, storage, mock_table):
        """UT-B7: get_response 使用精確查詢（含 created_at）"""
        mock_table.get_item.return_value = {
            "Item": {"trace_id": "trace-001", "mode": "GENERATE"}
        }
        result = storage.get_response("trace-001", "2026-04-30T00:00:00")
        mock_table.get_item.assert_called_once_with(
            Key={"trace_id": "trace-001", "created_at": "2026-04-30T00:00:00"}
        )
        assert result["trace_id"] == "trace-001"

    def test_get_response_latest(self, storage, mock_table):
        """UT-B8: get_response 不傳 created_at 時取最新一筆（query）"""
        mock_table.query.return_value = {
            "Items": [{"trace_id": "trace-001", "mode": "GENERATE"}]
        }
        result = storage.get_response("trace-001")
        # 驗證 query 條件：PK = trace-001, SK descending, limit 1
        call_kwargs = mock_table.query.call_args[1]
        assert call_kwargs["Limit"] == 1
        assert call_kwargs["ScanIndexForward"] is False
        assert result["trace_id"] == "trace-001"

    def test_get_response_not_found(self, storage, mock_table):
        """UT-B9: 不存在的 trace_id 回傳 None"""
        mock_table.query.return_value = {"Items": []}
        result = storage.get_response("non-existent")
        assert result is None

    def test_save_error(self, storage, mock_table):
        """UT-B10: save_error 正常寫入"""
        item = {
            "trace_id": "err-001",
            "error_code": "SVC_001",
            "error_message": "test error",
            "created_at": "2026-04-30T00:00:00",
        }
        result = storage.save_error(item)
        assert result is True
        mock_table.put_item.assert_called_once_with(Item=item)

    def test_save_error_without_trace_id(self, storage, mock_table):
        """UT-B11: 缺少 trace_id 回傳 False"""
        result = storage.save_error({"error_code": "SVC_001"})
        assert result is False
        mock_table.put_item.assert_not_called()

    def test_list_errors_all(self, storage, mock_table):
        """UT-B12: list_errors 不指定 code 時 scan"""
        mock_table.scan.return_value = {
            "Items": [
                {"trace_id": "e1", "error_code": "SVC_001"},
                {"trace_id": "e2", "error_code": "SVC_002"},
            ]
        }
        results = storage.list_errors(limit=10)
        assert len(results) == 2
        assert results[0]["error_code"] == "SVC_001"

    def test_list_errors_by_code(self, storage, mock_table):
        """UT-B13: list_errors 指定 error_code 時 query GSI"""
        mock_table.query.return_value = {
            "Items": [{"trace_id": "e1", "error_code": "SVC_001"}]
        }
        results = storage.list_errors(error_code="SVC_001")
        assert len(results) == 1
        # 驗證使用 GSI
        call_kwargs = mock_table.query.call_args[1]
        assert call_kwargs["IndexName"] == "error_code-index"

    def test_list_by_organ(self, storage, mock_table):
        """UT-B14: list_by_organ 使用 GSI 查詢"""
        mock_table.query.return_value = {
            "Items": [
                {"trace_id": "t1", "organ_no": "org-A"},
                {"trace_id": "t2", "organ_no": "org-A"},
            ]
        }
        results = storage.list_by_organ("org-A")
        assert len(results) == 2
        # 驗證使用 GSI
        call_kwargs = mock_table.query.call_args[1]
        assert call_kwargs["IndexName"] == "organ_no-index"
        # 驗證查詢條件
        from boto3.dynamodb.conditions import Key
        expr = call_kwargs["KeyConditionExpression"]
        assert expr is not None
