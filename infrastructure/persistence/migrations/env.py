"""
Alembic 迁移环境配置

复用 infrastructure/config/settings.py 的配置，支持：
- 同步迁移（SQLite dev）
- 异步迁移（PostgreSQL staging/prod）
- SQLite batch 模式（ALTER TABLE 支持）
"""

import sys
from logging.config import fileConfig
from pathlib import Path

# 将项目根目录添加到 Python 路径
# 这样才能导入 infrastructure 等模块
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from alembic import context
from sqlalchemy import pool, engine_from_config
from sqlmodel import SQLModel

# ========== 复用项目配置 ==========
# 从 settings.py 获取数据库 URL，保持配置统一
from infrastructure.config.settings import get_settings

settings = get_settings()

# Alembic Config 对象
config = context.config

# 设置日志（如果 alembic.ini 配置了的话）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ========== SQLModel 元数据 ==========
# 必须先导入所有 SQLModel 持久化模型，让它们注册到 SQLModel.metadata
#
# 注意：导入的是 infrastructure 层的 SQLModel 模型，不是 domain 层的实体！
# - 领域实体 (dataclass): domain/entities/  <- 不要导入这个
# - 持久化模型 (SQLModel): infrastructure/persistence/models/  <- 导入这个
#
# 推荐做法：在 models/__init__.py 中统一导出所有模型
# 然后这里只需一行导入
#
# TODO: 当你添加了 SQLModel 模型后，在这里导入它们
# from infrastructure.persistence.models import UserModel, OrderModel

target_metadata = SQLModel.metadata


# ========== 数据库 URL ==========
def get_database_url() -> str:
    """
    获取同步数据库 URL（Alembic 需要同步 URL）

    将异步驱动转换为同步驱动：
    - sqlite+aiosqlite:// -> sqlite://
    - postgresql+asyncpg:// -> postgresql://
    """
    url = settings.database_url

    # 转换异步驱动为同步驱动
    url = url.replace("sqlite+aiosqlite://", "sqlite://")
    url = url.replace("postgresql+asyncpg://", "postgresql://")

    # 对于 SQLite 文件数据库，确保目录存在
    if url.startswith("sqlite:///") and url != "sqlite:///:memory:":
        db_path = url.replace("sqlite:///", "")
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    return url


def is_sqlite() -> bool:
    """检查是否使用 SQLite"""
    return settings.database_url.startswith("sqlite")


# ========== 离线迁移 ==========
def run_migrations_offline() -> None:
    """
    离线模式：生成 SQL 脚本而不实际连接数据库

    使用场景：
    - 生成 SQL 脚本给 DBA 审核
    - 无法直接访问数据库时

    命令: alembic upgrade head --sql
    """
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite 需要 batch 模式支持 ALTER TABLE
        render_as_batch=is_sqlite(),
        # 检测列类型变化
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ========== 在线迁移 ==========
def run_migrations_online() -> None:
    """
    在线模式：直接连接数据库执行迁移

    统一使用同步模式（Alembic 本身是同步设计的）
    - SQLite: 使用内置 sqlite3 驱动
    - PostgreSQL: 使用 psycopg2 驱动（需安装 psycopg2-binary）
    """
    # 获取 alembic 配置，覆盖 sqlalchemy.url
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite 需要 batch 模式（不支持 ALTER TABLE）
            render_as_batch=is_sqlite(),
            # 检测列类型变化
            compare_type=True,
            # 检测服务器默认值变化（可选，可能产生噪音）
            # compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ========== 入口点 ==========
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
