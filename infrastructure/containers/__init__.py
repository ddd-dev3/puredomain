"""
依赖注入容器（异步版）

两层容器架构：
- InfraContainer: 基础设施（配置、异步数据库、UoW、仓储）
- AppContainer: 应用层（Mediator、Handlers）

使用 Bootstrap 作为组合根，连接所有容器。

使用示例：
    from infrastructure.containers import bootstrap, get_unit_of_work

    # 初始化
    boot = bootstrap()

    # 获取配置
    settings = boot.infra.settings()

    # 获取工作单元（异步）
    async with get_unit_of_work() as uow:
        # 业务逻辑
        await uow.commit()
"""

from .infrastructure import InfraContainer, get_request_session, set_request_session
from .application import AppContainer
from .bootstrap import (
    Bootstrap,
    bootstrap,
    get_bootstrap,
    get_settings,
    get_unit_of_work,
    get_session_factory,
)

__all__ = [
    # 容器
    "InfraContainer",
    "AppContainer",
    "Bootstrap",
    # 便捷函数
    "bootstrap",
    "get_bootstrap",
    "get_settings",
    "get_unit_of_work",
    "get_session_factory",
    # Session 上下文
    "get_request_session",
    "set_request_session",
]
