# DDD Framework

Python 领域驱动设计（DDD）基础框架 - 开箱即用的 DDD 架构模板

## ✨ 特性

- 🏗️ **完整的 DDD 分层架构**：Domain、Application、Infrastructure 层清晰分离
- 🔄 **多环境自动切换**：test/dev 用 SQLite，staging/prod 用 Supabase，零配置
- 💉 **依赖注入容器**：基于 dependency-injector，管理所有依赖
- 🧪 **测试友好**：测试环境自动使用 SQLite 内存数据库，超快速
- 📦 **CQRS 模式**：基于 mediatr-py，Command/Query 与 Handler 同文件组织
- 📝 **自动化日志横切**：HTTP/Handler/Repository 三层自动日志，代码零侵入
- 🗃️ **数据库迁移**：集成 Alembic，支持 autogenerate

---

## 📁 框架结构

```
project/
├── domain/                      # 🏛️ 领域层（核心业务逻辑）
│   ├── common/                  # 领域基础类
│   │   ├── base_entity.py       # 实体基类
│   │   ├── base_aggregate.py    # 聚合根基类
│   │   ├── base_value_object.py # 值对象基类
│   │   └── exceptions.py        # 领域异常
│   └── <your_domain>/           # 你的业务领域
│       ├── entities/
│       ├── repositories/        # 仓储接口（抽象）
│       └── value_objects/
│
├── application/                 # 📦 应用层（CQRS 按领域组织）
│   └── <your_domain>/
│       ├── commands/            # 命令 + 处理器
│       │   └── create_xxx.py    # Command + Handler 同文件
│       ├── queries/             # 查询 + 处理器（可选）
│       │   └── get_xxx.py
│       └── services/            # 领域服务（可选）
│
├── infrastructure/              # ⚙️ 基础设施层（技术实现）
│   ├── persistence/
│   │   ├── database_factory.py  # 数据库工厂（多环境自动切换）
│   │   ├── logging_mixin.py     # Repository 日志混入
│   │   └── migrations/          # Alembic 数据库迁移
│   ├── config/
│   │   └── settings.py
│   ├── containers/              # 依赖注入容器
│   │   ├── bootstrap.py         # 启动器
│   │   ├── application.py       # 应用容器 + wire_handlers()
│   │   └── infrastructure.py    # 基础设施容器
│   ├── logging/                 # 日志横切（集中管理）
│   │   ├── logger_factory.py    # 日志工厂（Loguru/Logfire）
│   │   ├── handler_behavior.py  # Handler 日志 Behavior
│   │   └── repository_mixin.py  # Repository 日志 Mixin
│   ├── mediator/
│   │   └── setup.py             # MediatorFactory
│   └── repositories/            # 仓储实现
│
├── interfaces/                  # 🌐 接口层
│   └── api/
│       ├── app.py               # App 入口
│       ├── middleware/
│       │   └── logging_middleware.py  # HTTP 请求日志
│       └── routes/
│
└── alembic.ini                  # 数据库迁移配置
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
uv sync
```

## 📖 核心用法

### 1️⃣ 定义 Command + Handler（同文件）

```python
@dataclass
class CreateOrderCommand:
    """创建订单命令"""
    customer_id: str
    product_id: str
    quantity: int

@dataclass
class CreateOrderResult:
    """命令执行结果"""
    success: bool
    order_id: Optional[str] = None
    message: str = ""

@Mediator.handler
class CreateOrderHandler:
    """命令处理器"""

    def __init__(self, order_repository, event_publisher):
        self._repository = order_repository
        self._event_publisher = event_publisher

    async def handle(self, request: CreateOrderCommand) -> CreateOrderResult:
        # 业务逻辑...
        order = Order.create(request.customer_id, request.product_id, request.quantity)
        await self._repository.save(order)
        return CreateOrderResult(success=True, order_id=str(order.id))
```

### 2️⃣ 定义 Query + Handler（同文件）与以上相同

```

### 3️⃣ 注册 Handler（需要 DI 时）

```python
class ApplicationContainer(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()

    # Handler Providers
    create_order_handler = providers.Factory(
        CreateOrderHandler,
        order_repository=infrastructure.order_repository,
        event_publisher=infrastructure.event_publisher,
    )

    get_order_handler = providers.Factory(
        GetOrderHandler,
        order_repository=infrastructure.order_repository,
    )

def wire_handlers(mediator, container):
    """注册需要 DI 的 Handler"""
    handler_map = {
        CreateOrderHandler: container.create_order_handler,
        GetOrderHandler: container.get_order_handler,
    }
    mediator.handler_class_manager = lambda cls, **_: handler_map.get(cls, lambda: cls())()
```

### 4️⃣ 路由中使用 Mediator

```python
# interfaces/api/routes/orders.py
from fastapi import APIRouter, Depends
from mediatr import Mediator
from application.order.commands.create_order import CreateOrderCommand
from interfaces.api.dependencies import get_mediator

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("")
async def create_order(
    request: CreateOrderRequest,
    mediator: Mediator = Depends(get_mediator),
):
    command = CreateOrderCommand(
        customer_id=request.customer_id,
        product_id=request.product_id,
        quantity=request.quantity,
    )
    result = await mediator.send_async(command)
    return result
```

---

## 🔧 环境配置

### 多环境数据库自动切换

| 环境 | 数据库 | 特点 |
|------|--------|------|
| **test** | SQLite 内存 | 超快速，用于测试 |
| **dev** | SQLite 文件 | 持久化，用于开发 |
| **staging** | Supabase | 预发布测试 |
| **prod** | Supabase | 生产环境 |

```bash
export APP_ENV=dev  # 自动使用 SQLite
export APP_ENV=prod # 自动使用 Supabase
```

### 智能日志系统

| 环境 | 日志后端 | 特点 |
|------|----------|------|
| **test / dev** | Loguru | 彩色输出，本地调试 |
| **staging / prod** | Logfire | 云端监控，分布式追踪 |

```python
from infrastructure.logging import get_logger
logger = get_logger(__name__)
logger.info("Hello!")  # 自动选择后端
```

### 自动化日志横切

框架提供三层自动日志，无需手动编写日志代码：

| 层 | 组件 | 日志内容 |
|---|---|---|
| HTTP | `LoggingMiddleware` | 请求方法、路径、状态码、耗时 |
| Handler | `LoggingBehavior` | Command/Query 名称、执行时间 |
| Repository | `LoggingRepositoryMixin` | CRUD 操作记录 |

**示例输出：**
```
14:30:46 | INFO | [abc123] -> POST /api/orders
14:30:46 | INFO | >> CreateOrderCommand executing...
14:30:46 | DEBUG | OrderRepository.add(Order)
14:30:46 | INFO | << CreateOrderCommand completed 24ms
14:30:46 | INFO | [abc123] <- 201 Created 26ms
```

**Repository 使用 Mixin（可选）：**
```python
from infrastructure.logging.repository_mixin import LoggingRepositoryMixin

class OrderRepository(LoggingRepositoryMixin, SqlAlchemyRepository):
    pass  # 自动有 CRUD 日志
```

---

### 数据库迁移（Alembic）

```bash
# 生成迁移（自动检测模型变化）
uv run alembic revision --autogenerate -m "add user table"

# 执行迁移
uv run alembic upgrade head

# 回滚
uv run alembic downgrade -1

# 查看当前版本
uv run alembic current
```

---

## ❓ FAQ

### 何时需要 wire_handlers？

| 场景 | 是否需要 |
|------|---------|
| Handler 无 `__init__` 参数 | ❌ 不需要（自动注册） |
| Handler 需要 Repository/Service | ✅ 需要 |
| 简单函数形式 Handler | ❌ 不需要 |

### 为什么 Command 和 Handler 放同一文件？

- 它们总是一起修改
- 减少文件跳转

### Handler 的 handle 方法参数命名

按 mediatr-py 官方风格，统一使用 `request`：

```python
def handle(self, request: CreateOrderCommand):
```

### 数据库模型使用 SQLModel
### 不用 Provide 注解用显式指定

---

## 📄 许可证

MIT License
