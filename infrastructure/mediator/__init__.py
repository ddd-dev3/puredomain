"""
Mediator 模块

CQRS 中介者模式实现
"""

from .setup import (
    MediatorFactory,
    get_mediator_factory,
    create_mediator,
    register_handler,
)

__all__ = [
    "MediatorFactory",
    "get_mediator_factory",
    "create_mediator",
    "register_handler",
]
