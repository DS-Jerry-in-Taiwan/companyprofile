"""
錯誤日誌記錄器
============
包裝 storage.save_error() 提供簡化的錯誤記錄 API

Phase 24: 錯誤記錄功能
"""

import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ErrorLogger:
    """錯誤日誌記錄器"""

    def __init__(self):
        self._storage = None
        self._init_storage()

    def _init_storage(self):
        """初始化 storage"""
        if self._storage is None:
            try:
                import os
                import json as json_lib
                
                # 正確的路徑計算：src/functions/utils → 專案根目錄/config
                self_dir = os.path.dirname(os.path.abspath(__file__))  # src/functions/utils
                src_dir = os.path.dirname(self_dir)  # src/functions
                src_parent = os.path.dirname(src_dir)  # src
                project_root = os.path.dirname(src_parent)  # 專案根目錄
                config_path = os.path.join(project_root, "config", "storage_config.json")
                
                with open(config_path) as f:
                    cfg = json_lib.load(f)
                env = cfg.get("default", "development")
                storage_cfg = cfg["storage"][env]
                
                from src.storage.factory import StorageFactory
                self._storage = StorageFactory.create(storage_cfg)
                logger.info(f"ErrorLogger storage initialized from {config_path}")
            except Exception as e:
                logger.warning(f"ErrorLogger storage init failed, error logging disabled: {e}")
                self._storage = None

    def save_error(
        self,
        trace_id: str,
        organ_no: Optional[str] = None,
        organ_name: Optional[str] = None,
        error_code: str = "UNKNOWN",
        error_message: str = "",
        error_phase: str = "unknown",
        recoverable: int = 1,
        request_payload: Optional[dict] = None,
        mode: Optional[str] = None,
        optimization_mode: Optional[str] = None,
    ) -> bool:
        """儲存錯誤到 DB"""
        if self._storage is None:
            logger.warning("Storage not available, cannot save error log")
            return False

        try:
            item = {
                "trace_id": trace_id,
                "organ_no": organ_no,
                "organ_name": organ_name,
                "error_code": error_code,
                "error_message": error_message,
                "error_phase": error_phase,
                "recoverable": recoverable,
                "request_payload": json.dumps(request_payload) if request_payload else None,
                "mode": mode,
                "optimization_mode": optimization_mode,
                "created_at": datetime.now().isoformat(),
            }

            self._storage.save_error(item)
            return True

        except Exception as e:
            logger.error(f"Failed to save error: {e}")
            return False