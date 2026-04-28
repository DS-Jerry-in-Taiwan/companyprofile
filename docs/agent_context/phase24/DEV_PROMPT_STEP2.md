# Phase 24 Step 2 开发提示

## 1. 角色定位

你是后端开发工程师，负责实作存储层抽象接口。

---

## 2. 任务目标

**Step 2: 建立抽象层 (StorageInterface)**

- 在 `src/storage/base.py` 定义存储抽象接口
- 定义 3 个抽象方法

---

## 3. 参考文件

| 文件 | 路径 |
|------|------|
| 开发计划 | `docs/agent_context/phase24/DEVELOPMENT_PLAN.md` |
| 任务边界 | `docs/agent_context/phase24/TASK_BOUNDARIES.md` |
| 开发日志 | `docs/agent_context/phase24/DEVELOPMENT_LOG.md` |
| Step 1 完成 | 目录结构已建立 |

---

## 4. 执行流程

### 4.1 实作抽象接口

写入 `src/storage/base.py`：

```python
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

### 4.2 测试

```bash
# 测试命令
python -c "
from src.storage.base import StorageInterface
print('抽象方法:', StorageInterface.__abstractmethods__)
"

# 预期结果
抽象方法: frozenset({'save_response', 'get_response', 'list_by_organ'})
```

### 4.3 验证清单

| 检查项 | 标准 |
|--------|------|
| `StorageInterface` 类存在 | ✅ |
| 继承 `ABC` | ✅ |
| `save_response` 抽象方法 | ✅ |
| `get_response` 抽象方法 | ✅ |
| `list_by_organ` 抽象方法 | ✅ |
| 方法签名正确 | ✅ |

---

## 5. 完成后回报

请报告：

1. **执行结果**：`base.py` 内容
2. **测试结果**：抽象方法列表是否正确
3. **验证检查**：6 个检查项是否都通过
4. **更新状态**：DEVELOPMENT_LOG.md 是否已更新

---

**不要 git commit**，等待确认后再继续 Step 3。