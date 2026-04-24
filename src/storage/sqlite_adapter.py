from typing import Optional
from sqlalchemy import Column, String, Integer, Text, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker
from .base import StorageInterface

Base = declarative_base()


class LLMResponse(Base):
    __tablename__ = "llm_responses"

    request_id = Column(String, primary_key=True)
    trace_id = Column(String)
    organ_no = Column(String, index=True)
    mode = Column(String)  # GENERATE / OPTIMIZE

    # Prompt
    prompt_raw = Column(Text)

    # Prompt framework metadata (Phase 23 diversity guidance)
    prompt_structure_key = Column(String)   # "traditional" | "service_first" | ...
    prompt_opening_key   = Column(String)   # "industry" | "market" | ...
    prompt_sentence_key  = Column(String)   # "service" | "feature" | ...
    prompt_template_name = Column(String)   # "concise" | "standard" | "detailed"

    # Response
    response_raw = Column(Text)
    response_processed = Column(Text)
    is_json = Column(Integer, default=0)
    word_count = Column(Integer)
    tokens_used = Column(Integer)
    model = Column(String)
    latency_ms = Column(Integer)

    # Metadata
    created_at = Column(String, index=True)
    duration_ms = Column(Integer)


class SQLiteStorage(StorageInterface):
    """SQLite 存储适配器"""

    def __init__(self, connection: str):
        self.engine = create_engine(connection)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_response(self, item: dict) -> bool:
        session = self.Session()
        try:
            session.add(LLMResponse(**item))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_response(self, request_id: str) -> Optional[dict]:
        session = self.Session()
        try:
            result = session.get(LLMResponse, request_id)
            if result is None:
                return None
            data = {c.name: getattr(result, c.name) for c in result.__table__.columns}
            return data
        finally:
            session.close()

    def list_by_organ(self, organ_no: str) -> list[dict]:
        session = self.Session()
        try:
            stmt = select(LLMResponse).where(LLMResponse.organ_no == organ_no)
            results = session.execute(stmt).scalars().all()
            return [
                {c.name: getattr(r, c.name) for c in r.__table__.columns}
                for r in results
            ]
        finally:
            session.close()
