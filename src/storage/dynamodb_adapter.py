"""
DynamoDB 儲存配接器

使用 boto3 操作 DynamoDB，適合 Lambda 環境。
表格透過 serverless.yml 的 CloudFormation 管理，adapter 不自動建表。

表格設計：
  {stage}-llm-responses
    PK: trace_id (String)
    SK: created_at (String)
    GSI: organ_no-index  (organ_no → ALL)
    GSI: status-index    (status → KEYS_ONLY)

  {stage}-error-logs
    PK: trace_id (String)
    SK: created_at (String)
    GSI: error_code-index (error_code → ALL)
"""

import boto3
import logging
from datetime import datetime, timezone
from typing import Optional

from .base import StorageInterface

logger = logging.getLogger(__name__)


class DynamoDBStorage(StorageInterface):
    """DynamoDB 存储适配器"""

    def __init__(
        self,
        llm_responses_table: str,
        error_logs_table: str,
        quality_logs_table: str = None,
        region: str = "ap-northeast-1",
    ):
        self.region = region
        self.llm_responses_table_name = llm_responses_table
        self.error_logs_table_name = error_logs_table
        self.quality_logs_table_name = quality_logs_table
        self._client = None  # lazy init

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.resource("dynamodb", region_name=self.region)
        return self._client

    @property
    def responses_table(self):
        return self.client.Table(self.llm_responses_table_name)

    @property
    def errors_table(self):
        return self.client.Table(self.error_logs_table_name)

    @property
    def quality_logs(self):
        return self.client.Table(self.quality_logs_table_name)

    def save_response(self, item: dict) -> bool:
        """保存 LLM 响应到 DynamoDB"""
        if "trace_id" not in item:
            logger.warning("save_response: missing trace_id, skipping")
            return False

        if "created_at" not in item:
            item["created_at"] = datetime.now(timezone.utc).isoformat()

        self.responses_table.put_item(Item=item)
        logger.info(
            f"DYNAMODB WRITE | table={self.llm_responses_table_name} "
            f"trace_id={item.get('trace_id')} "
            f"organ_no={item.get('organ_no')} mode={item.get('mode')}"
        )
        return True

    def get_response(self, trace_id: str, created_at: str = None) -> Optional[dict]:
        """根據 trace_id 取得響應

        Args:
            trace_id: 查詢的 trace_id
            created_at: 可選，指定時間戳精確查詢；不傳時回傳最新一筆

        Returns:
            dict or None
        """
        if created_at:
            result = self.responses_table.get_item(
                Key={"trace_id": trace_id, "created_at": created_at}
            )
            return result.get("Item")

        # 只靠 PK 查，取最新一筆 (SK descending, limit 1)
        from boto3.dynamodb.conditions import Key
        response = self.responses_table.query(
            KeyConditionExpression=Key("trace_id").eq(trace_id),
            ScanIndexForward=False,
            Limit=1,
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def list_by_organ(self, organ_no: str) -> list[dict]:
        """根據 organ_no 查詢（使用 GSI）"""
        from boto3.dynamodb.conditions import Key

        response = self.responses_table.query(
            IndexName="organ_no-index",
            KeyConditionExpression=Key("organ_no").eq(organ_no),
        )
        return response.get("Items", [])

    def save_error(self, item: dict) -> bool:
        """儲存錯誤日誌到 DynamoDB"""
        if "trace_id" not in item:
            logger.warning("save_error: missing trace_id, skipping")
            return False
        if "created_at" not in item:
            item["created_at"] = datetime.now(timezone.utc).isoformat()

        self.errors_table.put_item(Item=item)
        logger.info(
            f"DYNAMODB ERROR | table={self.error_logs_table_name} "
            f"trace_id={item.get('trace_id')} error_code={item.get('error_code')}"
        )
        return True

    def list_errors(self, limit: int = 100, error_code: str = None) -> list[dict]:
        """查詢錯誤日誌"""
        from boto3.dynamodb.conditions import Key

        if error_code:
            response = self.errors_table.query(
                IndexName="error_code-index",
                KeyConditionExpression=Key("error_code").eq(error_code),
                Limit=limit,
            )
        else:
            response = self.errors_table.scan(Limit=limit)

        return response.get("Items", [])

    def save_quality_log(self, item: dict) -> bool:
        """保存品質閘門重試日誌 (Phase 40)"""
        if "trace_id" not in item:
            logger.warning("save_quality_log: missing trace_id, skipping")
            return False
        if "created_at" not in item:
            item["created_at"] = datetime.now(timezone.utc).isoformat()

        self.quality_logs.put_item(Item=item)
        logger.info(
            f"DYNAMODB QUALITY LOG | table={self.quality_logs_table_name} "
            f"trace_id={item.get('trace_id')} "
            f"retry_count={item.get('retry_count')} "
            f"final_result={item.get('final_result')}"
        )
        return True
