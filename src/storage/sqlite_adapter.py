from typing import Optional
import os
import logging
from sqlalchemy import Column, String, Integer, Text, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker
from .base import StorageInterface

Base = declarative_base()
logger = logging.getLogger(__name__)


class LLMResponse(Base):
    __tablename__ = "llm_responses"

    # Surrogate key
    id = Column(Integer, primary_key=True, autoincrement=True)

    trace_id = Column(String, index=True)
    status = Column(String, default="success")  # success / error
    error_code = Column(String, nullable=True)   # SVC_001, INVALID_REQUEST, etc.
    organ_no = Column(String, index=True)
    organ_name = Column(String)  # 公司名稱
    company_url = Column(String)  # 公司官網
    mode = Column(String)  # GENERATE / OPTIMIZE
    optimization_mode = Column(String)  # CONCISE / STANDARD / DETAILED

    # User Input（使用者輸入的資料）
    user_input = Column(Text)

    # Prompt
    prompt_raw = Column(Text)

    # Prompt framework metadata (Phase 23 diversity guidance)
    prompt_structure_key = Column(String)   # "traditional" | "service_first" | ...
    prompt_opening_key   = Column(String)   # "industry" | "market" | ...
    prompt_sentence_key  = Column(String)   # "service" | "feature" | ...
    prompt_template_name = Column(String)   # "concise" | "standard" | "detailed"

    # Response
    response_raw = Column(Text)
    is_json = Column(Integer, default=0)
    word_count = Column(Integer)
    tokens_used = Column(Integer)
    model = Column(String)
    latency_ms = Column(Integer)

    # Metadata
    created_at = Column(String, index=True)
    duration_ms = Column(Integer)


class ErrorLog(Base):
    """錯誤日誌表 - 用於除錯與監控"""
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String, index=True)
    organ_no = Column(String, index=True)
    organ_name = Column(String)
    
    # Error Information
    error_code = Column(String, index=True)  # SVC_001, LLM_429, etc.
    error_message = Column(Text)  # 錯誤訊息
    error_phase = Column(String)  # search_node, generate_node, post_processing, etc.
    recoverable = Column(Integer)  # 1 = 可復原, 0 = 不可復原
    
    # Request Info
    request_payload = Column(Text)  # 請求的 JSON
    mode = Column(String)  # GENERATE / OPTIMIZE
    optimization_mode = Column(String)  # CONCISE / STANDARD / DETAILED
    
    # Timestamp
    created_at = Column(String, index=True)


class SQLiteStorage(StorageInterface):
    """SQLite 存储适配器"""

    def __init__(self, connection: str):
        # 排除 :memory: 和絕對路徑，只處理相對路徑
        if connection.startswith("sqlite:///") and not connection.endswith(":memory:"):
            db_path = connection.replace("sqlite:///", "")
            if not os.path.isabs(db_path):
                _self_dir = os.path.dirname(os.path.abspath(__file__))
                _project_root = os.path.dirname(os.path.dirname(_self_dir))
                resolved = os.path.join(_project_root, db_path)
                connection = f"sqlite:///{resolved}"
        self.engine = create_engine(connection)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_response(self, item: dict) -> bool:
        session = self.Session()
        try:
            session.add(LLMResponse(**item))
            session.commit()
            logger.info(
                f"DB WRITE | id={item.get('id')} trace_id={item.get('trace_id')} "
                f"organ_no={item.get('organ_no')} mode={item.get('mode')} "
                f"model={item.get('model')} tokens={item.get('tokens_used')} "
                f"latency={item.get('latency_ms')}ms word_count={item.get('word_count')}"
            )
            return True
        except Exception as e:
            session.rollback()
            logger.warning(
                f"DB WRITE FAILED | trace_id={item.get('trace_id')} "
                f"organ_no={item.get('organ_no')} error={e}"
            )
            raise e
        finally:
            session.close()

    def get_response(self, trace_id: str) -> Optional[dict]:
        session = self.Session()
        try:
            stmt = select(LLMResponse).where(LLMResponse.trace_id == trace_id)
            result = session.execute(stmt).scalar_one_or_none()
            if result is None:
                logger.info(f"DB READ | trace_id={trace_id} → not found")
                return None
            data = {c.name: getattr(result, c.name) for c in result.__table__.columns}
            logger.info(
                f"DB READ | trace_id={trace_id} "
                f"organ_no={data.get('organ_no')} mode={data.get('mode')} "
                f"word_count={data.get('word_count')}"
            )
            return data
        except Exception as e:
            logger.warning(f"DB READ FAILED | trace_id={trace_id} error={e}")
            raise e
        finally:
            session.close()

    def list_by_organ(self, organ_no: str) -> list[dict]:
        session = self.Session()
        try:
            stmt = select(LLMResponse).where(LLMResponse.organ_no == organ_no)
            results = session.execute(stmt).scalars().all()
            logger.info(
                f"DB LIST | organ_no={organ_no} count={len(results)}"
            )
            return [
                {c.name: getattr(r, c.name) for c in r.__table__.columns}
                for r in results
            ]
        except Exception as e:
            logger.warning(f"DB LIST FAILED | organ_no={organ_no} error={e}")
            raise e
        finally:
            session.close()

    def save_error(self, item: dict) -> bool:
        """儲存錯誤日誌"""
        session = self.Session()
        try:
            session.add(ErrorLog(**item))
            session.commit()
            logger.info(
                f"ERROR LOG | trace_id={item.get('trace_id')} "
                f"error_code={item.get('error_code')} phase={item.get('error_phase')}"
            )
            return True
        except Exception as e:
            session.rollback()
            logger.warning(
                f"ERROR LOG FAILED | trace_id={item.get('trace_id')} error={e}"
            )
            raise e
        finally:
            session.close()

    def list_errors(self, limit: int = 100, error_code: str = None) -> list[dict]:
        """查詢錯誤日誌"""
        session = self.Session()
        try:
            stmt = select(ErrorLog).order_by(ErrorLog.created_at.desc())
            if error_code:
                stmt = stmt.where(ErrorLog.error_code == error_code)
            stmt = stmt.limit(limit)
            results = session.execute(stmt).scalars().all()
            logger.info(f"ERROR LIST | count={len(results)}")
            return [
                {c.name: getattr(r, c.name) for c in r.__table__.columns}
                for r in results
            ]
        except Exception as e:
            logger.warning(f"ERROR LIST FAILED | error={e}")
            raise e
        finally:
            session.close()
