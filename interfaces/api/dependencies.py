"""
API 依赖注入

提供 FastAPI 路由使用的依赖函数。
"""

from typing import Optional, Callable
from mediatr import Mediator


# ============ Mediator 依赖 ============

_mediator_getter: Optional[Callable[[], Mediator]] = None


def set_mediator_getter(getter: Callable[[], Mediator]) -> None:
    """
    设置 Mediator 获取器（由 DI 容器调用）

    在应用启动时配置，将 DI 容器的 mediator provider 注入。
    """
    global _mediator_getter
    _mediator_getter = getter


def get_mediator() -> Mediator:
    """
    获取 Mediator 实例（FastAPI 依赖）

    用法：
        @router.post("/accounts")
        async def create(cmd: CreateCmd, mediator: Mediator = Depends(get_mediator)):
            return await mediator.send_async(cmd)
    """
    if _mediator_getter is None:
        raise RuntimeError(
            "Mediator not configured. Call set_mediator_getter() at startup."
        )
    return _mediator_getter()
