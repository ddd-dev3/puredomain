"""
Handler 层日志 Behavior

自动记录所有 Command/Query 的执行：
- 执行开始
- 执行成功和耗时
- 执行失败和异常信息
"""

import time
from typing import Any, Callable, Awaitable

from infrastructure.logging import get_logger

logger = get_logger(__name__)


class LoggingBehavior:
    """
    日志 Behavior

    在 Handler 执行前后自动记录日志。
    作为 mediatr 的 pipeline behavior 使用。
    """

    async def handle(
        self,
        request: Any,
        next_handler: Callable[[], Awaitable[Any]]
    ) -> Any:
        """
        执行 behavior 逻辑

        Args:
            request: Command 或 Query 对象
            next_handler: 调用下一个 behavior 或实际 handler 的函数
        """
        request_name = type(request).__name__
        start = time.perf_counter()

        logger.info(f">> {request_name} executing...")

        try:
            result = await next_handler()

            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(f"<< {request_name} completed {duration_ms:.0f}ms")

            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(f"<< {request_name} failed: {type(e).__name__}: {e} {duration_ms:.0f}ms")
            raise


def register_logging_behavior() -> None:
    """
    注册日志 Behavior 到 mediatr

    必须在应用启动时调用，且在注册 handler 之前。
    """
    from typing import Any
    import mediatr

    # 注册为全局 behavior（适用于所有 Command/Query）
    if Any not in mediatr.__behaviors__:
        mediatr.__behaviors__[Any] = []

    # 避免重复注册
    if LoggingBehavior not in mediatr.__behaviors__[Any]:
        mediatr.__behaviors__[Any].insert(0, LoggingBehavior)
        logger.debug("LoggingBehavior registered")
