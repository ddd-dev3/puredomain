"""
基础设施容器（InfraContainer）- 异步版

管理所有基础设施组件：配置、数据库、工作单元、仓储实现等。
已整合原 ConfigContainer 的功能。

使用示例：
    # 1. 定义仓储实现
    from infrastructure.repositories.user_repository import SqlAlchemyUserRepository

    # 2. 在 InfraContainer 中注册
    user_repository = providers.Factory(
        SqlAlchemyUserRepository,
        session_factory=db_session_factory
    )
"""

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from contextvars import ContextVar

from infrastructure.config.settings import Settings
from infrastructure.persistence.database_factory import DatabaseFactory
from infrastructure.persistence.unit_of_work import UnitOfWork


# 请求级别的 AsyncSession 上下文变量
_request_session: ContextVar[AsyncSession | None] = ContextVar("request_session", default=None)


def get_request_session() -> AsyncSession | None:
    """获取当前请求的 AsyncSession"""
    return _request_session.get()


def set_request_session(session: AsyncSession | None) -> None:
    """设置当前请求的 AsyncSession"""
    _request_session.set(session)


class InfraContainer(containers.DeclarativeContainer):
    """基础设施容器 - 管理配置和技术实现（异步版）"""

    # ============ 配置 ============

    # 应用配置（单例）
    settings = providers.Singleton(Settings)

    # 便捷访问常用配置
    app_env = providers.Callable(
        lambda s: s.app_env,
        s=settings
    )

    database_url = providers.Callable(
        lambda s: s.database_url,
        s=settings
    )

    debug = providers.Callable(
        lambda s: s.debug,
        s=settings
    )

    # ============ 异步数据库 ============

    # 异步数据库引擎（单例）
    db_engine: providers.Singleton[AsyncEngine] = providers.Singleton(
        DatabaseFactory.create_engine
    )

    # 异步 Session 工厂（单例）
    db_session_factory: providers.Singleton[async_sessionmaker[AsyncSession]] = providers.Singleton(
        DatabaseFactory.create_session_factory,
        engine=db_engine
    )

    # ============ 工作单元 ============

    # 工作单元（每次请求新实例）
    unit_of_work = providers.Factory(
        UnitOfWork,
        session_factory=db_session_factory
    )

    # ============ 在此添加你的仓储 ============
    # 示例：
    # user_repository = providers.Factory(
    #     SqlAlchemyUserRepository,
    #     session_factory=db_session_factory
    # )

    # ============ 在此添加你的领域服务 ============
    # 示例：
    # email_sender = providers.Singleton(
    #     SmtpEmailSender,
    #     config=settings
    # )
