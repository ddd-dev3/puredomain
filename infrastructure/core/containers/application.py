"""
应用容器（AppContainer）

管理应用层组件：Mediator、命令/查询处理器、应用服务等。
依赖 InfraContainer 获取基础设施。

Handler 注册流程：
1. 在此容器中定义 Handler 的 Provider
2. 在 wire_handlers() 中注册到 MediatorFactory
3. Mediator 会自动从容器获取 Handler 实例（依赖已注入）

使用示例：
    # 1. 定义 Handler
    from application.handlers.user_handlers import CreateUserHandler

    # 2. 在 AppContainer 中注册 Provider
    create_user_handler = providers.Factory(
        CreateUserHandler,
        uow=infra.unit_of_work
    )

    # 3. 在 wire_handlers() 中注册到 MediatorFactory
    factory.register_handler(CreateUserHandler, container.create_user_handler)
"""

from typing import TYPE_CHECKING
from dependency_injector import containers, providers

from infrastructure.core.mediator import create_mediator, get_mediator_factory

# 导入示例 Handlers（可删除）
from application.handlers.example_handlers import CreateUserHandler

if TYPE_CHECKING:
    from .infrastructure import InfraContainer


class AppContainer(containers.DeclarativeContainer):
    """应用容器 - 管理应用层服务"""

    # 依赖配置容器
    config = providers.DependenciesContainer()

    # 依赖基础设施容器
    infra = providers.DependenciesContainer()

    # ============ Mediator ============
    mediator = providers.Singleton(create_mediator)

    # ============ 示例处理器（可删除）============
    create_user_handler = providers.Factory(
        CreateUserHandler,
        uow=infra.unit_of_work
    )

    # ============ 在此添加你的 Handler ============
    # 示例：
    # your_command_handler = providers.Factory(
    #     YourCommandHandler,
    #     repository=infra.your_repository,
    # )
    #
    # your_query_handler = providers.Factory(
    #     YourQueryHandler,
    #     repository=infra.your_repository,
    # )


def wire_handlers(container: AppContainer) -> None:
    """将 Handler Provider 注册到 MediatorFactory

    在此函数中注册所有的 Handler，以便 Mediator 可以分发命令/查询。
    """
    factory = get_mediator_factory()

    # 示例 Handler（可删除）
    factory.register_handler(CreateUserHandler, container.create_user_handler)

    # ============ 在此注册你的 Handler ============
    # 示例：
    # factory.register_handler(YourCommandHandler, container.your_command_handler)
    # factory.register_handler(YourQueryHandler, container.your_query_handler)
