---
project_name: 'puredomain'
user_name: 'Alex'
date: '2025-12-28'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
existing_patterns_found: 8
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | >= 3.12 | 运行时 |
| FastAPI | >= 0.122.0 | Web 框架 |
| SQLAlchemy | >= 2.0.44 | ORM（异步模式） |
| dependency-injector | >= 4.48.2 | 依赖注入容器 |
| mediatr | >= 1.3.2 | CQRS Mediator 模式 |
| pydantic-settings | >= 2.12.0 | 配置管理 |
| loguru | >= 0.7.3 | 日志（本地） |
| alembic | >= 1.14.0 | 数据库迁移 |
| pytest | >= 8.0.0 | 测试框架 |
| pytest-asyncio | >= 0.23.0 | 异步测试支持 |

---

## Critical Implementation Rules

### CQRS + Mediator 模式

- **Command + Handler 必须在同一文件** - 垂直切片架构，减少文件跳转
- **使用 `await mediator.send_async(command)`** 发送命令/查询
- **Handler 的 handle 方法参数统一命名为 `request`**：
  ```python
  async def handle(self, request: CreateOrderCommand) -> CreateOrderResult:
  ```
- **Handler 需要依赖注入时，必须在容器中注册**

### 异步优先

- **所有数据库操作必须是异步的** - 使用 `async/await`
- **使用 `AsyncSession`**，不使用同步 Session
- **Repository 方法必须是 `async def`**

### DDD 分层架构

```
domain/          # 领域层 - 纯业务逻辑，无框架依赖
application/     # 应用层 - CQRS Commands/Queries + Handlers
infrastructure/  # 基础设施层 - 技术实现（DB、外部服务）
interfaces/      # 接口层 - API 端点
```

- **Domain 层不能依赖 Infrastructure 层**
- **Repository 接口定义在 Domain 层，实现在 Infrastructure 层**

### 依赖注入

- **使用 dependency-injector 容器管理依赖**
- **不使用 `@Provide` 注解，使用显式 Provider 指定**
- **Bootstrap 是组合根，连接所有容器**：
  ```python
  boot = bootstrap()
  uow = boot.infra.unit_of_work()
  mediator = boot.app.mediator()
  ```

### 工作单元模式 (Unit of Work)

- **使用 `async with UnitOfWork()` 管理事务边界**：
  ```python
  async with boot.infra.unit_of_work() as uow:
      # 业务逻辑
      await uow.commit()
  ```
- **异常时自动回滚**

### CQRS Pipeline Behaviors（横切关注点）

框架提供完整的 Pipeline Behaviors，**自动处理验证、异常、事务、日志**：

| 顺序 | Behavior | 作用 |
|------|----------|------|
| 1 | `ValidationBehavior` | 自动验证 Command/Query 参数（Pydantic） |
| 2 | `ExceptionBehavior` | 捕获异常并转换为统一格式 |
| 3 | `TransactionBehavior` | Command 自动包装 savepoint |
| 4 | `LoggingBehavior` | 自动记录执行日志 |

- **Handler 只需写业务逻辑**：验证、事务、异常、日志全自动
- **领域异常自动转换**：`DomainException` → HTTP 状态码 + 统一 JSON 格式
- **链路追踪**：所有日志包含 `request_id`，可追踪完整请求链路

```python
# Handler 示例 - 只写业务！
class CreateUserHandler:
    async def handle(self, request: CreateUserCommand):
        user = User(name=request.name)
        await self._uow.users.add(user)
        return user.id
        # 验证、事务、异常、日志 —— Pipeline 自动处理
```

### 自动化日志横切

框架提供三层自动日志，**无需在代码中手动编写日志**：

| 层 | 组件 | 说明 |
|---|---|---|
| HTTP | `LoggingMiddleware` | 自动记录请求/响应（含 request_id） |
| Handler | `LoggingBehavior` | 自动记录 Command/Query 执行（含 request_id） |
| Repository | `LoggingRepositoryMixin` | 可选混入，记录 CRUD 操作（含 request_id） |

- **不要在 Handler 中手动写日志**：已有 LoggingBehavior 自动记录
- **Repository 日志是可选的**：继承 `LoggingRepositoryMixin` 即可启用
- **日志使用 `infrastructure.logging.get_logger()`**
- **request_id 贯穿全链路**：便于问题排查

### 数据库迁移 (Alembic)

- **迁移文件位置**: `infrastructure/persistence/migrations/versions/`
- **生成迁移**: `uv run alembic revision --autogenerate -m "描述"`
- **执行迁移**: `uv run alembic upgrade head`
- **SQLModel 模型需在 `env.py` 中导入**才能被 autogenerate 检测

### Entity 和 Aggregate

- **Entity 使用 `@dataclass(eq=False)`**
- **Entity 基于 ID 进行相等性比较**
- **AggregateRoot 继承 BaseEntity，管理领域事件**
- **使用 `add_domain_event()` 添加事件，`pull_domain_events()` 获取并清除**

---

## Testing Rules

- **测试文件命名**: `test_*.py`
- **测试类命名**: `Test*`
- **测试函数命名**: `test_*`
- **使用 `asyncio_mode = "auto"`** - 自动处理异步测试
- **测试环境自动使用 SQLite 内存数据库**

---

## Code Quality & Style

### 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 文件 | snake_case | `create_order.py` |
| 类 | PascalCase | `CreateOrderCommand` |
| 函数/方法 | snake_case | `async def handle()` |
| 常量 | UPPER_SNAKE | `MAX_RETRY_COUNT` |

### 文档字符串

- **使用中文文档字符串**（项目语言偏好）
- **类和公共方法必须有 docstring**

---

## Environment Configuration

| 环境 | 数据库 | 日志 |
|------|--------|------|
| test | SQLite 内存 | Loguru |
| dev | SQLite 文件 | Loguru |
| staging | Supabase | Logfire |
| prod | Supabase | Logfire |

- **通过 `APP_ENV` 环境变量切换**
- **配置使用 pydantic-settings，自动从 `.env` 读取**

---

## Critical Don't-Miss Rules

### MUST DO

- [ ] Command/Query + Handler 放同一文件
- [ ] 使用 `await mediator.send_async()` 而非 `send()`
- [ ] Handler 参数命名为 `request`
- [ ] 数据库操作使用 `async/await`
- [ ] 使用 `async with UnitOfWork()` 管理事务

### MUST NOT

- [ ] 不要在 Domain 层引入框架依赖
- [ ] 不要使用同步数据库操作
- [ ] 不要跳过依赖注入直接实例化 Handler
- [ ] 不要忘记在容器中注册需要 DI 的 Handler
