"""
数据库工厂 - 根据环境自动选择数据库（异步版）

基于 SQLModel + SQLAlchemy async 实现。

支持环境：
- test: SQLite 内存数据库（快速测试）
- dev: SQLite 文件数据库（本地开发）
- staging/prod: Supabase/PostgreSQL（生产环境）
"""

import os
from typing import Literal, Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool, NullPool
from sqlmodel import SQLModel

Environment = Literal["test", "dev", "staging", "prod"]


class DatabaseFactory:
    """数据库工厂 - 统一的异步数据库创建接口"""

    @staticmethod
    def create_engine(env: Optional[Environment] = None) -> AsyncEngine:
        """
        根据环境创建异步数据库引擎

        Args:
            env: 环境类型，如果不指定则从环境变量 APP_ENV 读取

        Returns:
            SQLAlchemy AsyncEngine 实例
        """
        if env is None:
            env = DatabaseFactory.get_current_env()

        if env == "test":
            return DatabaseFactory._create_test_engine()
        elif env == "dev":
            return DatabaseFactory._create_dev_engine()
        elif env == "staging":
            return DatabaseFactory._create_supabase_engine("staging")
        elif env == "prod":
            return DatabaseFactory._create_supabase_engine("prod")
        else:
            raise ValueError(f"Unknown environment: {env}")

    @staticmethod
    def _create_test_engine() -> AsyncEngine:
        """
        测试环境：SQLite 内存数据库（异步）

        特点：
        - 超快速（在内存中）
        - 每次运行都是全新的
        - 适合单元测试和集成测试
        """
        return create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # 内存数据库使用静态连接池
        )

    @staticmethod
    def _create_dev_engine() -> AsyncEngine:
        """
        开发环境：SQLite 文件数据库（异步）

        特点：
        - 数据持久化到文件
        - 方便本地调试
        - 适合本地开发
        """
        db_path = os.getenv("DEV_DB_PATH", "data/dev.db")

        # 确保目录存在
        import pathlib
        pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        return create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )

    @staticmethod
    def _create_supabase_engine(env: str) -> AsyncEngine:
        """
        生产环境：Supabase (PostgreSQL) 异步

        Args:
            env: 'staging' 或 'prod'

        环境变量：
        - STAGING_DATABASE_URL: staging 环境数据库 URL
        - PROD_DATABASE_URL: prod 环境数据库 URL

        URL 格式：
        postgresql+asyncpg://user:password@host:port/database
        """
        env_var = f"{env.upper()}_DATABASE_URL"
        db_url = os.getenv(env_var)

        if not db_url:
            raise ValueError(
                f"Missing database URL for {env} environment. "
                f"Please set environment variable: {env_var}"
            )

        # 将 postgresql:// 转换为 postgresql+asyncpg://
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return create_async_engine(
            db_url,
            pool_size=int(os.getenv(f"{env.upper()}_DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv(f"{env.upper()}_DB_MAX_OVERFLOW", "20")),
            pool_pre_ping=True,
            echo=False,
        )

    @staticmethod
    def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        """
        创建异步 Session 工厂

        Args:
            engine: SQLAlchemy AsyncEngine

        Returns:
            async_sessionmaker 实例
        """
        return async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    @staticmethod
    def get_current_env() -> Environment:
        """
        获取当前环境

        Returns:
            环境类型（test/dev/staging/prod）
        """
        env = os.getenv("APP_ENV", "dev")

        if env not in ["test", "dev", "staging", "prod"]:
            raise ValueError(
                f"Invalid APP_ENV value: {env}. "
                f"Must be one of: test, dev, staging, prod"
            )

        return env

    @staticmethod
    def get_database_url(env: Optional[Environment] = None) -> str:
        """
        获取当前环境的数据库 URL（用于显示或日志）

        Args:
            env: 环境类型

        Returns:
            数据库连接字符串（隐藏密码）
        """
        if env is None:
            env = DatabaseFactory.get_current_env()

        if env == "test":
            return "sqlite+aiosqlite:///:memory:"
        elif env == "dev":
            return f"sqlite+aiosqlite:///{os.getenv('DEV_DB_PATH', 'data/dev.db')}"
        else:
            env_var = f"{env.upper()}_DATABASE_URL"
            url = os.getenv(env_var, "")
            # 隐藏密码
            if url and "@" in url:
                parts = url.split("@")
                user_part = parts[0].split("://")[0] + "://***:***"
                return user_part + "@" + parts[1]
            return url or f"<未设置 {env_var}>"


# 便捷函数

def get_engine(env: Optional[Environment] = None) -> AsyncEngine:
    """便捷函数：创建异步数据库引擎"""
    return DatabaseFactory.create_engine(env)


def get_session_factory(env: Optional[Environment] = None) -> async_sessionmaker[AsyncSession]:
    """便捷函数：创建异步 Session 工厂"""
    engine = get_engine(env)
    return DatabaseFactory.create_session_factory(engine)


async def init_database(engine: Optional[AsyncEngine] = None) -> None:
    """
    初始化数据库（创建所有表）- 异步版

    在应用启动时调用，自动创建所有 SQLModel 模型对应的表。
    如果表已存在则跳过。

    Args:
        engine: SQLAlchemy AsyncEngine，如果不传则自动创建

    使用示例：
        # 1. 先导入所有模型（确保注册到 SQLModel.metadata）
        from your_app.models import User, Post, Comment

        # 2. 初始化数据库
        await init_database(engine)
    """
    if engine is None:
        engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
