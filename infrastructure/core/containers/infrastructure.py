"""
基础设施容器（InfraContainer）

管理所有基础设施组件：数据库、工作单元、仓储实现等。
依赖 ConfigContainer 获取配置。

使用示例：
    # 1. 定义仓储实现
    from infrastructure.repositories.user_repository import SqlAlchemyUserRepository

    # 2. 在 InfraContainer 中注册
    user_repository = providers.Factory(
        SqlAlchemyUserRepository,
        session=db_session
    )
"""

from dependency_injector import containers, providers
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker, Session
from contextvars import ContextVar

from infrastructure.core.database.database_factory import DatabaseFactory
from infrastructure.core.database.unit_of_work import UnitOfWork
from .config import ConfigContainer


# 请求级别的 Session 上下文变量
_request_session: ContextVar[Session | None] = ContextVar("request_session", default=None)


def get_request_session() -> Session | None:
    """获取当前请求的 Session"""
    return _request_session.get()


def set_request_session(session: Session | None) -> None:
    """设置当前请求的 Session"""
    _request_session.set(session)


class InfraContainer(containers.DeclarativeContainer):
    """基础设施容器 - 管理技术实现"""

    # 依赖配置容器
    config = providers.DependenciesContainer()

    # ============ 数据库 ============

    # 数据库引擎（单例）
    db_engine: providers.Singleton[Engine] = providers.Singleton(
        DatabaseFactory.create_engine
    )

    # Session 工厂（单例）
    db_session_factory: providers.Singleton[sessionmaker] = providers.Singleton(
        DatabaseFactory.create_session_factory,
        engine=db_engine
    )

    # ============ 工作单元 ============

    # 工作单元（每次请求新实例）
    unit_of_work = providers.Factory(
        UnitOfWork,
        session_factory=db_session_factory
    )

    # ============ 数据库 Session ============

    # 数据库 Session
    # 优先使用请求级别的 Session（由 middleware 管理）
    # 如果没有（如后台任务），则创建新的 Session
    db_session = providers.Factory(
        lambda session_factory: get_request_session() or session_factory(),
        session_factory=db_session_factory
    )

    # ============ 在此添加你的仓储 ============
    # 示例：
    # user_repository = providers.Factory(
    #     SqlAlchemyUserRepository,
    #     session=db_session
    # )

    # ============ 在此添加你的领域服务 ============
    # 示例：
    # email_sender = providers.Singleton(
    #     SmtpEmailSender,
    #     config=config.settings
    # )
