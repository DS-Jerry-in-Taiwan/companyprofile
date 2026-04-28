# Phase 24 开发计划

## 版本
- **文件版本**: v0.1.0
- **建立日期**: 2026-04-24
- **目标版本**: v0.4.0

---

## 开发步骤总览

```
Step 1: 建立目录结构
    ↓
Step 2: 建立抽象层 (StorageInterface)
    ↓
Step 3: 单元测试抽象层
    ↓
Step 4: SQLite 适配方实作
    ↓
Step 5: 单元测试 SQLite
    ↓
Step 6: 工廠层实作 (StorageFactory)
    ↓
Step 7: 单元测试工廠
    ↓
Step 8: 配置层实作
    ↓
Step 9: 集成测试
    ↓
Step 10: LLM 服务集成
    ↓
Step 11: 最终验收
```

---

## Step 1: 建立目录结构

### 目标
- 建立 `src/storage/` 目录结构
- 创建基础的 Python 模块文件

### 完成标准

| 标准 | 说明 |
|------|------|
| 目录创建 | `src/storage/` 存在 |
| `__init__.py` | 创建空文件 |
| `base.py` | 创建抽象接口文件 |
| `factory.py` | 创建工廠文件 |
| `sqlite_adapter.py` | 创建 SQLite 适配器文件 |

### 测试指标

```bash
# 测试命令
ls -la src/storage/
python -c "import src.storage"

# 预期结果
目录存在且可导入
```

### 完成后更新

- [ ] DEVELOPMENT_LOG.md: Step 1 状态更新
- [ ] 目录结构确认

---

## Step 2: 建立抽象层 (StorageInterface)

### 目标
- 定义存储抽象接口
- 所有存储适配器必须实现此接口

### 接口定义

```python
# storage/base.py
from abc import ABC, abstractmethod
from typing import Optional

class StorageInterface(ABC):
    """存储抽象接口"""
    
    @abstractmethod
    def save_response(self, item: dict) -> bool:
        """保存 LLM 响应"""
        pass
    
    @abstractmethod
    def get_response(self, request_id: str) -> Optional[dict]:
        """根据 request_id 获取响应"""
        pass
    
    @abstractmethod
    def list_by_organ(self, organ_no: str) -> list[dict]:
        """根据 organ_no 列表响应"""
        pass
```

### 完成标准

| 标准 | 说明 |
|------|------|
| StorageInterface 类存在 | 定义在 base.py |
| 3 个抽象方法 | save_response, get_response, list_by_organ |
| 抽象方法签名 | 参数和返回值类型正确 |

### 测试指标

```bash
# 测试命令
python -c "from src.storage.base import StorageInterface; print(StorageInterface.__abstractmethods__)"

# 预期结果
('save_response', 'get_response', 'list_by_organ')
```

### 完成后更新

- [ ] DEVELOPMENT_LOG.md: Step 2 状态更新
- [ ] `src/storage/base.py` 创建完成
- [ ] TASK_BOUNDARIES.md 更细边界

---

## Step 3: 单元测试抽象层

### 目标
- 测试 StorageInterface 可以被正确继承
- 测试子类必须实现所有抽象方法

### 测试用例

| 用例 | 说明 |
|------|------|
| UT-03-01 | 继承 StorageInterface 必须实现 save_response |
| UT-03-02 | 继承 StorageInterface 必须实现 get_response |
| UT-03-03 | 继承 StorageInterface 必须实现 list_by_organ |
| UT-03-04 | 不实现抽象方法会 raise TypeError |

### 完成标准

| 标准 | 说明 |
|------|------|
| 4 个测试用例 | 全部通过 |
| TypeError 测试 | 不实现会抛出异常 |

### 测试指标

```bash
# 测试命令
pytest tests/test_storage_base.py -v

# 预期结果
4 passed
```

### 完成后更新

- [ ] `tests/test_storage_base.py` 创建
- [ ] 4 个测试用例通过
- [ ] DEVELOPMENT_LOG.md 更新

---

## Step 4: SQLite 适配方实作

### 目标
- 实现 SQLiteStorage 适配器
- 使用 SQLAlchemy 定义 schema

### schema 定义

```python
# storage/sqlite_adapter.py
from sqlalchemy import Column, String, Integer, Text, Index, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class LLMResponse(Base):
    __tablename__ = 'llm_responses'
    
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
    def __init__(self, connection: str):
        self.engine = create_engine(connection)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save_response(self, item: dict) -> bool:
        session = self.Session()
        session.add(LLMResponse(**item))
        session.commit()
        return True
    
    def get_response(self, request_id: str) -> Optional[dict]:
        session = self.Session()
        result = session.query(LLMResponse).get(request_id)
        return result.__dict__ if result else None
    
    def list_by_organ(self, organ_no: str) -> list[dict]:
        session = self.Session()
        results = session.query(LLMResponse).filter_by(organ_no=organ_no).all()
        return [r.__dict__ for r in results]
```

### 完成标准

| 标准 | 说明 |
|------|------|
| SQLiteStorage 类存在 | 定义在 sqlite_adapter.py |
| 继承 StorageInterface | 实现所有抽象方法 |
| SQLAlchemy schema | 7 个字段定义 |
| 自动建表 | __init__ 时 create_all |

### 测试指标

```bash
# 测试命令
python -c "from src.storage.sqlite_adapter import SQLiteStorage, LLMResponse; print('ok')"

# 预期结果
无错误输出
```

### 完成后更新

- [ ] `src/storage/sqlite_adapter.py` 创建完成
- [ ] DEVELOPMENT_LOG.md 更新

---

## Step 5: 单元测试 SQLite

### 目标
- 测试 SQLiteStorage 的 CRUD 操作

### 测试用例

| 用例 | 说明 |
|------|------|
| UT-05-01 | save_response() 保存数据 |
| UT-05-02 | get_response() 取回数据 |
| UT-05-03 | get_response() 不存在返回 None |
| UT-05-04 | list_by_organ() 返回列表 |
| UT-05-05 | 保存后能取回相同数据 |

### 完成标准

| 标准 | 说明 |
|------|------|
| 5 个测试用例 | 全部通过 |
| 数据一致性 | save 后能 get 回来 |

### 测试指标

```bash
# 测试命令
pytest tests/test_sqlite_adapter.py -v

# 预期结果
5 passed
```

### 完成后更新

- [ ] `tests/test_sqlite_adapter.py` 创建
- [ ] 5 个测试用例通过
- [ ] DEVELOPMENT_LOG.md 更新

---

## Step 6: 工廠层实作 (StorageFactory)

### 目标
- 实现工廠模式
- 根据配置创建对应存储适配器

### 工廠定义

```python
# storage/factory.py
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
```

### 完成标准

| 标准 | 说明 |
|------|------|
| StorageFactory 类存在 | 定义在 factory.py |
| create() 方法 | 根据 type 创建适配器 |
| 错误处理 | 未知 type 抛出异常 |

### 测试指标

```bash
# 测试命令
python -c "from src.storage.factory import StorageFactory; print(StorageFactory)"

# 预期结果
无错误输出
```

### 完成后更新

- [ ] `src/storage/factory.py` 创建完成
- [ ] DEVELOPMENT_LOG.md 更新

---

## Step 7: 单元测试工廠

### 目标
- 测试 StorageFactory 的创建逻辑

### 测试用例

| 用例 | 说明 |
|------|------|
| UT-07-01 | create("sqlite") 返回 SQLiteStorage |
| UT-07-02 | create("unknown") 抛出 ValueError |
| UT-07-03 | create() 使用默认 type |

### 完成标准

| 标准 | 说明 |
|------|------|
| 3 个测试用例 | 全部通过 |
| 类型正确 | 返回正确的适配器类 |

### 测试指标

```bash
# 测试命令
pytest tests/test_storage_factory.py -v

# 预期结果
3 passed
```

### 完成后更新

- [ ] `tests/test_storage_factory.py` 创建
- [ ] 3 个测试用例通过
- [ ] DEVELOPMENT_LOG.md 更新

---

## Step 8: 配置层实作

### 目标
- 创建存储配置文件
- 支持开发/生产环境切换

### 配置文件

```json
// config/storage_config.json
{
  "storage": {
    "development": {
      "type": "sqlite",
      "connection": "sqlite:///data/llm_responses.db"
    }
  },
  "default": "development"
}
```

### 完成标准

| 标准 | 说明 |
|------|------|
| 配置文件存在 | config/storage_config.json |
| JSON 格式正确 | 无语法错误 |
| SQLite 配置 | 有效的连接字符串 |

### 测试指标

```bash
# 测试命令
python -c "import json; f=open('config/storage_config.json'); json.load(f)"

# 预期结果
无错误输出
```

### 完成后更新

- [ ] `config/storage_config.json` 创建
- [ ] DEVELOPMENT_LOG.md 更新
- [ ] requirements.txt 可能需要添加 SQLAlchemy

---

## Step 9: 集成测试

### 目标
- 测试完整流程：从配置创建到存储

### 测试用例

| 用例 | 说明 |
|------|------|
| IT-09-01 | 配置 → 工廠 → 存储完整流程 |
| IT-09-02 | save → get 完整流程 |
| IT-09-03 | 数据一致性 |

### 完成标准

| 标准 | 说明 |
|------|------|
| 3 个集成测试 | 全部通过 |
| 端到端 | 配置到存储到取回 |

### 测试指标

```bash
# 测试命令
pytest tests/test_storage_integration.py -v

# 预期结果
3 passed
```

### 完成后更新

- [ ] `tests/test_storage_integration.py` 创建
- [ ] 3 个集成测试通过
- [ ] DEVELOPMENT_LOG.md 更新

---

## Step 10: LLM 服务集成

### 目标
- 在 llm_service.py 中集成存储
- LLM 响应后自动保存

### 集成位置

```python
# 在 llm_service.py 中
from src.storage.factory import StorageFactory
import json

# 启动时加载配置
config = json.load(open("config/storage_config.json"))
storage = StorageFactory.create(config["storage"][config["default"]])

# 使用示例
def call_llm(prompt):
    response = llm.invoke(prompt)
    
    # 保存原始响应
    storage.save_response({
        "request_id": "req-123",
        "prompt": prompt,
        "response": response,
        "created_at": "2026-04-24T..."
    })
    
    return response
```

### 完成标准

| 标准 | 说明 |
|------|------|
| llm_service.py 导入 StorageFactory | 无导入错误 |
| save_response() 调用 | 可选调用 |
| 配置加载 | 使用 config/storage_config.json |

### 测试指标

```bash
# 测试命令
python -c "from src.functions.api_controller import app; print('ok')"

# 预期结果
无导入错误
```

### 里程碑

- [ ] `src/storage/` 模块完整
- [ ] LLM 服务可调用存储
- [ ] DEVELOPMENT_LOG.md 更新

---

## Step 11: 最终验收

### 验收清单

| 项目 | 标准 |
|------|------|
| 单元测试 | >= 15 个通过 |
| 集成测试 | >= 3 个通过 |
| 回归测试 | 不破坏现有功能 |
| 配置文件 | 格式正确 |
| 文档更新 | DEVELOPMENT_LOG.md 完成 |

### 验收标准

| 标准 | 说明 |
|------|------|
| 所有步骤 | 全部完成 |
| 单元测试覆盖率 | >= 80% |
| 文档完整性 | 100% |
| 版本 | v0.4.0 |

### 最终状态

- [ ] Phase 24 结案
- [ ] 目标版本: v0.4.0 达成

---

## 任务边界与禁止事项

### 明确的任务边界

| 范围 | 说明 |
|------|------|
| 主要目标 | LLM 响应存储层 |
| 职责 | 抽象存储接口 + SQLite 实作 |
| 预留给 | PostgreSQL / DynamoDB / S3 |

### 禁止事项

| 项目 | 说明 |
|------|------|
| 不修改现有 API 响应格式 | LLMOutput schema 维持不变 |
| 不修改 error handling | 维持 Phase 21 标准 |
| 不修改后处理逻辑 | 不破坏 Phase 22 |
| 存储失败不影响主流程 | 调用加 try-catch |
| 不强制存储 | 配置可选 |

---

## 版本控制

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1.0 | 2026-04-24 | 初始版本 |
| v0.4.0 | - | 完成目标 |

---

## 审查清单

在提交 PR 前，确认以下项目：

- [ ] Step 1: 目录结构
- [ ] Step 2: 抽象层定义
- [ ] Step 3: 抽象层测试 (4 passed)
- [ ] Step 4: SQLite 适配器
- [ ] Step 5: SQLite 测试 (5 passed)
- [ ] Step 6: 工廠层
- [ ] Step 7: 工廠测试 (3 passed)
- [ ] Step 8: 配置文件
- [ ] Step 9: 集成测试 (3 passed)
- [ ] Step 10: LLM 服务集成
- [ ] Step 11: 最终验收
- [ ] 版本更新至 v0.4.0
- [ ] DEVELOPMENT_LOG.md 更新