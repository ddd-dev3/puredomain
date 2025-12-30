"""
CQRS Pipeline Behaviors

横切关注点的统一管理模块。

Pipeline 执行顺序（从外到内）：
1. ValidationBehavior  - 验证请求参数
2. ExceptionBehavior   - 异常捕获和转换
3. TransactionBehavior - 事务管理（savepoint）
4. LoggingBehavior     - 日志记录
5. Handler             - 实际业务逻辑

使用方式：
    from infrastructure.behaviors import register_all_behaviors

    # 在应用启动时调用
    register_all_behaviors()
"""

from .validation_behavior import (
    ValidationBehavior,
    ValidationException,
    register_validation_behavior,
)
from .exception_behavior import (
    ExceptionBehavior,
    ApplicationException,
    ApplicationError,
    register_exception_behavior,
)
from .transaction_behavior import (
    TransactionBehavior,
    Command,
    is_command,
    register_transaction_behavior,
)

from infrastructure.logging import get_logger

logger = get_logger(__name__)


def register_all_behaviors() -> None:
    """
    注册所有 Pipeline Behaviors

    必须在应用启动时、创建 Mediator 之前调用。
    注册顺序决定了执行顺序（先注册的先执行）。
    """
    # 按顺序注册（先注册的在 pipeline 最外层）
    register_validation_behavior()   # 1. 验证
    register_exception_behavior()    # 2. 异常处理
    register_transaction_behavior()  # 3. 事务
    # LoggingBehavior 在 handler_behavior.py 中单独注册

    logger.info("All pipeline behaviors registered")


__all__ = [
    # Behaviors
    "ValidationBehavior",
    "ExceptionBehavior",
    "TransactionBehavior",
    # Exceptions
    "ValidationException",
    "ApplicationException",
    "ApplicationError",
    # Utilities
    "Command",
    "is_command",
    # Registration
    "register_all_behaviors",
    "register_validation_behavior",
    "register_exception_behavior",
    "register_transaction_behavior",
]
