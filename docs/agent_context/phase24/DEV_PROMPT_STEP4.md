# Phase 24 Step 4 开发提示

## 1. 角色定位

你是后端开发工程师，负责实作 SQLite 存储适配器。

---

## 2. 任务目标

**Step 4: SQLite 适配方实作**

- 使用 SQLAlchemy 定义 `llm_responses` schema
- 实现 `StorageInterface` 的 3 个方法

---

## 3. 参考文件

| 文件 | 路径 |
|------|------|
| 开发计划 | `docs/agent_context/phase24/DEVELOPMENT_PLAN.md` |
| 抽象层 | `src/storage/base.py` |
| 任务边界 | `docs/agent_context/phase24/TASK_BOUNDARIES.md` |
| 开发日志 | `docs/agent_context/phase24/DEVELOPMENT_LOG.md` |

---

## 4. 执行流程

### 4.1 实作 SQLiteStorage

写入 `src/storage/sqlite_adapter.py`：

```python
from typing import Optional
from sqlalchemy import Column, String, Integer, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .base import StorageInterface

Base = declarative_base()


class LLMResponse(Base):
    __tablename__ = "llm_responses"

    request_id = Column(String, primary_key=True)
    trace_id = Column(String)
    organ_no = Column(String, index=True)
    mode = Column(String)  # DETAILED / BRIEF

    # Prompt
    prompt_raw = Column(Text)
    prompt_with_guidance = Column(Text)

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
            result = session.query(LLMResponse).get(request_id)
            if result is None:
                return None
            data = {c.name: getattr(result, c.name) for c in result.__table__.columns}
            return data
        finally:
            session.close()

    def list_by_organ(self, organ_no: str) -> list[dict]:
        session = self.Session()
        try:
            results = session.query(LLMResponse).filter_by(organ_no=organ_no).all()
            return [
                {c.name: getattr(r, c.name) for c in r.__table__.columns}
                for r in results
            ]
        finally:
            session.close()
```

### 4.2 测试

```bash
# 测试命令
python -c "
from src.storage.sqlite_adapter import SQLiteStorage, LLMResponse
print('✅ SQLiteStorage 可导入')
print('✅ LLMResponse schema 可导入')
"

# 预期结果
✅ SQLiteStorage 可导入
✅ LLMResponse schema 可导入
```

### 4.3 验证清单

| 检查项 | 标准 |
|--------|------|
| SQLAlchemy schema 定义 | ✅ |
| LLMResponse 表 12+ 字段 | ✅ |
| SQLiteStorage 实现 save_response | ✅ |
| SQLiteStorage 实现 get_response | ✅ |
| SQLiteStorage 实现 list_by_organ | ✅ |
| 错误回滚 | ✅ try/except/rollback |

---

## 5. 完成后回报

请报告：

1. **执行结果**：sqlite_adapter.py 内容确认
2. **测试结果**：导入成功？
3. **验证检查**：6 个检查项是否都通过
4. **更新状态**：DEVELOPMENT_LOG.md 是否已更新

---

**不要 git commit**，等待确认后再继续 Step 5。