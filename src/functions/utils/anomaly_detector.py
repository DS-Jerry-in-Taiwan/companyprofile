#!/usr/bin/env python3
"""
異常偵測模組
實作自動異常偵測腳本和 E2E 流程異常通報機制
"""

import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalySeverity(Enum):
    """異常嚴重度分級"""

    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class AnomalyType(Enum):
    """異常類型"""

    SYSTEM_ERROR = "系統錯誤"
    NETWORK_TIMEOUT = "網路超時"
    DB_CONNECTION = "資料庫連線"
    API_FAILURE = "API失敗"
    RESOURCE_EXHAUSTION = "資源耗盡"
    DATA_VALIDATION = "資料驗證"
    AUTHENTICATION = "身份驗證"
    BUSINESS_LOGIC = "業務邏輯"


@dataclass
class AnomalyReport:
    """異常回報資料結構"""

    anomaly_id: str
    timestamp: str
    system: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    description: str
    trace_id: Optional[str] = None
    initial_analysis: Optional[str] = None
    suggested_action: Optional[str] = None
    reporter: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "anomaly_id": self.anomaly_id,
            "timestamp": self.timestamp,
            "system": self.system,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "trace_id": self.trace_id,
            "initial_analysis": self.initial_analysis,
            "suggested_action": self.suggested_action,
            "reporter": self.reporter,
            "resolved": self.resolved,
            "resolution_time": self.resolution_time,
        }


class AnomalyDetector:
    """異常偵測器"""

    def __init__(self):
        self.anomaly_reports: List[AnomalyReport] = []
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict[str, Dict]:
        """載入知識庫（模擬）"""
        return {
            "DB_TIMEOUT": {
                "symptoms": ["timeout", "connection", "database"],
                "action": "重啟DB連線/通報DBA",
                "escalation": False,
            },
            "API_RATE_LIMIT": {
                "symptoms": ["rate limit", "429", "too many requests"],
                "action": "實施退避策略/檢查API配額",
                "escalation": False,
            },
            "MEMORY_LEAK": {
                "symptoms": ["memory", "heap", "out of memory"],
                "action": "重啟服務/檢查記憶體使用",
                "escalation": True,
            },
        }

    def detect_anomaly_from_error(
        self, error_msg: str, system: str, trace_id: str = None
    ) -> Optional[AnomalyReport]:
        """從錯誤訊息偵測異常"""
        anomaly_type, severity = self._classify_error(error_msg)

        if anomaly_type:
            return self._create_anomaly_report(
                system=system,
                anomaly_type=anomaly_type,
                severity=severity,
                description=error_msg,
                trace_id=trace_id,
            )
        return None

    def _classify_error(
        self, error_msg: str
    ) -> tuple[Optional[AnomalyType], AnomalySeverity]:
        """分類錯誤類型和嚴重度"""
        error_lower = error_msg.lower()

        # 系統錯誤
        if any(
            keyword in error_lower
            for keyword in ["500", "internal server error", "crash", "exception"]
        ):
            return AnomalyType.SYSTEM_ERROR, AnomalySeverity.HIGH

        # 網路超時
        if any(
            keyword in error_lower
            for keyword in ["timeout", "connection timed out", "read timeout"]
        ):
            return AnomalyType.NETWORK_TIMEOUT, AnomalySeverity.MEDIUM

        # 資料庫連線
        if any(
            keyword in error_lower
            for keyword in [
                "database",
                "db",
                "connection refused",
                "mysql",
                "postgresql",
            ]
        ):
            return AnomalyType.DB_CONNECTION, AnomalySeverity.HIGH

        # API失敗
        if any(
            keyword in error_lower
            for keyword in ["api", "404", "403", "401", "bad request"]
        ):
            return AnomalyType.API_FAILURE, AnomalySeverity.MEDIUM

        # 資源耗盡
        if any(
            keyword in error_lower
            for keyword in ["memory", "disk", "cpu", "resource", "limit exceeded"]
        ):
            return AnomalyType.RESOURCE_EXHAUSTION, AnomalySeverity.HIGH

        # 資料驗證
        if any(
            keyword in error_lower
            for keyword in ["validation", "invalid", "format", "schema"]
        ):
            return AnomalyType.DATA_VALIDATION, AnomalySeverity.LOW

        # 身份驗證
        if any(
            keyword in error_lower
            for keyword in ["auth", "unauthorized", "forbidden", "token"]
        ):
            return AnomalyType.AUTHENTICATION, AnomalySeverity.MEDIUM

        return None, AnomalySeverity.LOW

    def _create_anomaly_report(
        self,
        system: str,
        anomaly_type: AnomalyType,
        severity: AnomalySeverity,
        description: str,
        trace_id: str = None,
    ) -> AnomalyReport:
        """建立異常回報"""
        anomaly_id = f"ANM-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 查找知識庫建議
        initial_analysis, suggested_action = self._analyze_with_knowledge_base(
            description
        )

        report = AnomalyReport(
            anomaly_id=anomaly_id,
            timestamp=timestamp,
            system=system,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            trace_id=trace_id,
            initial_analysis=initial_analysis,
            suggested_action=suggested_action,
            reporter="SYSTEM_AUTO",
        )

        self.anomaly_reports.append(report)
        self._notify_anomaly(report)

        return report

    def _analyze_with_knowledge_base(self, description: str) -> tuple[str, str]:
        """使用知識庫分析異常"""
        desc_lower = description.lower()

        for kb_key, kb_data in self.knowledge_base.items():
            if any(symptom in desc_lower for symptom in kb_data["symptoms"]):
                return f"匹配知識庫條目: {kb_key}", kb_data["action"]

        return "未找到匹配的知識庫條目", "需要人工分析"

    def _notify_anomaly(self, report: AnomalyReport):
        """異常通報"""
        logger.warning(
            f"[異常偵測] {report.severity.value}嚴重度異常: {report.anomaly_id}"
        )
        logger.info(f"系統: {report.system}, 類型: {report.anomaly_type.value}")
        logger.info(f"描述: {report.description}")

        if report.severity == AnomalySeverity.HIGH:
            logger.error(f"[緊急通報] 高嚴重度異常需要立即處理: {report.anomaly_id}")

    def get_anomaly_report(self, anomaly_id: str) -> Optional[AnomalyReport]:
        """取得特定異常回報"""
        for report in self.anomaly_reports:
            if report.anomaly_id == anomaly_id:
                return report
        return None

    def get_unresolved_anomalies(self) -> List[AnomalyReport]:
        """取得未解決的異常"""
        return [report for report in self.anomaly_reports if not report.resolved]

    def resolve_anomaly(self, anomaly_id: str, resolution_note: str = None) -> bool:
        """標記異常為已解決"""
        report = self.get_anomaly_report(anomaly_id)
        if report:
            report.resolved = True
            report.resolution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[異常解決] {anomaly_id} 已標記為解決")
            if resolution_note:
                logger.info(f"解決說明: {resolution_note}")
            return True
        return False

    def generate_anomaly_summary(self) -> Dict[str, Any]:
        """產生異常統計摘要"""
        total = len(self.anomaly_reports)
        unresolved = len(self.get_unresolved_anomalies())

        # 按嚴重度統計
        severity_stats = {}
        for severity in AnomalySeverity:
            count = len([r for r in self.anomaly_reports if r.severity == severity])
            severity_stats[severity.value] = count

        # 按類型統計
        type_stats = {}
        for anom_type in AnomalyType:
            count = len(
                [r for r in self.anomaly_reports if r.anomaly_type == anom_type]
            )
            type_stats[anom_type.value] = count

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_anomalies": total,
            "unresolved_anomalies": unresolved,
            "resolution_rate": round((total - unresolved) / total * 100, 2)
            if total > 0
            else 0,
            "severity_distribution": severity_stats,
            "type_distribution": type_stats,
        }


# 全域異常偵測器實例
anomaly_detector = AnomalyDetector()


def detect_and_report_anomaly(
    error_msg: str, system: str, trace_id: str = None
) -> Optional[str]:
    """偵測並回報異常，返回異常ID"""
    report = anomaly_detector.detect_anomaly_from_error(error_msg, system, trace_id)
    return report.anomaly_id if report else None


def get_anomaly_summary() -> Dict[str, Any]:
    """取得異常統計摘要"""
    return anomaly_detector.generate_anomaly_summary()
