# Phase 24 Step 1 开发提示

## 1. 角色定位

你是后端开发工程师，负责实作存储层模块。

---

## 2. 任务目标

**Step 1: 建立目录结构**

- 建立 `src/storage/` 目录
- 创建 4 个基础 Python 模块文件

---

## 3. 参考文件

| 文件 | 路径 |
|------|------|
| 开发计划 | `docs/agent_context/phase24/DEVELOPMENT_PLAN.md` |
| 任务边界 | `docs/agent_context/phase24/TASK_BOUNDARIES.md` |
| 开发日志 | `docs/agent_context/phase24/DEVELOPMENT_LOG.md` |

---

## 4. 执行流程

### 4.1 创建目录

```bash
mkdir -p src/storage
```

### 4.2 创建 4 个文件

```bash
# 1. __init__.py
touch src/storage/__init__.py

# 2. base.py - 创建空的 StorageInterface（后面 Step 2 实作）
touch src/storage/base.py

# 3. factory.py - 创建空的 StorageFactory（后面 Step 6 实作）
touch src/storage/factory.py

# 4. sqlite_adapter.py - 创建空的 SQLiteStorage（后面 Step 4 实作）
touch src/storage/sqlite_adapter.py
```

### 4.3 测试

```bash
# 测试命令
ls -la src/storage/
python -c "import src.storage"

# 预期结果
目录存在且可导入
```

### 4.4 验证清单

| 检查项 | 标准 |
|--------|------|
| `src/storage/` 目录存在 | ✅ |
| `__init__.py` 存在 | ✅ |
| `base.py` 存在 | ✅ |
| `factory.py` 存在 | ✅ |
| `sqlite_adapter.py` 存在 | ✅ |
| 可导入 `src.storage` | ✅ 无错误 |

### 4.5 更新文件

完成验证后，更新 `DEVELOPMENT_LOG.md`：

```markdown
### Step 1: 建立目录结构
- [x] Step 1: 建立 `src/storage/` 目录
- [x] 创建 4 个空模块文件
- [x] 测试通过 ✅
```

---

## 5. 完成后回报

请报告：

1. **执行结果**：目录和文件是否成功创建
2. **测试结果**：测试通过了吗？输出是什么？
3. **验证检查**：5 个检查项是否都通过
4. **更新状态**：DEVELOPMENT_LOG.md 是否已更新

---

**不要 git commit**，等待确认后再继续 Step 2。