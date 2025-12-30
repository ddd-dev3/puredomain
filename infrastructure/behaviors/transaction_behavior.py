"""
事务 Behavior

为 Command 提供自动事务管理：
- 使用 Savepoint 实现嵌套事务（与 DBSessionMiddleware 协作）
- Command 成功时释放 savepoint
- Command 失败时回滚到 savepoint
- Query 不参与事务管理（只读）

执行顺序：在 ExceptionBehavior 之后，LoggingBehavior 之前

设计说明：
- DBSessionMiddleware 管理请求级事务（最外层）
- TransactionBehavior 管理命令级事务（savepoint）
- 这样单个 Command 失败不会影响同一请求中的其他操作
"""

from typing import Any, Callable, Awaitable, Protocol, runtime_checkable

from infrastructure.logging import get_logger
from infrastructure.containers.infrastructure import get_request_session
from interfaces.api.middleware.logging_middleware import get_request_id

logger = get_logger(__name__)


@runtime_checkable
class Command(Protocol):
    """
    Command 标记协议

    实现此协议的请求会被 TransactionBehavior 包装在 savepoint 中。
    可以通过继承或命名约定（类名以 Command 结尾）来标识。
    """
    pass


def is_command(request: Any) -> bool:
    """
    判断请求是否是 Command

    判断规则：
    1. 实现了 Command 协议
    2. 类名以 'Command' 结尾
    """
    if isinstance(request, Command):
        return True
    return type(request).__name__.endswith("Command")


class TransactionBehavior:
    """
    事务 Behavior

    为 Command 提供 savepoint 级别的事务隔离。
    Query 直接透传，不参与事务管理。
    """

    async def handle(
        self,
        request: Any,
        next_handler: Callable[[], Awaitable[Any]]
    ) -> Any:
        """
        执行事务管理逻辑

        Args:
            request: Command 或 Query 对象
            next_handler: 调用下一个 behavior 或实际 handler 的函数
        """
        request_id = get_request_id() or "-"
        request_name = type(request).__name__

        # Query 不需要事务管理
        if not is_command(request):
            logger.debug(f"[{request_id}] {request_name} is Query, skipping transaction")
            return await next_handler()

        # 获取当前请求的 session
        session = get_request_session()

        if session is None:
            # 没有 session（可能是非 HTTP 上下文），直接执行
            logger.debug(f"[{request_id}] {request_name} no session, executing without transaction")
            return await next_handler()

        # 使用 savepoint 包装 Command 执行
        logger.debug(f"[{request_id}] {request_name} starting savepoint")

        try:
            # 开始 savepoint（嵌套事务）
            async with session.begin_nested():
                result = await next_handler()

            logger.debug(f"[{request_id}] {request_name} savepoint committed")
            return result

        except Exception as e:
            # savepoint 自动回滚
            logger.debug(
                f"[{request_id}] {request_name} savepoint rolled back: "
                f"{type(e).__name__}"
            )
            raise


def register_transaction_behavior() -> None:
    """
    注册事务 Behavior 到 mediatr

    必须在应用启动时调用。
    TransactionBehavior 应该在 ExceptionBehavior 之后执行。
    """
    from typing import Any
    import mediatr

    if Any not in mediatr.__behaviors__:
        mediatr.__behaviors__[Any] = []

    # 插入到位置 2（在 ValidationBehavior, ExceptionBehavior 之后）
    if TransactionBehavior not in mediatr.__behaviors__[Any]:
        insert_pos = min(2, len(mediatr.__behaviors__[Any]))
        mediatr.__behaviors__[Any].insert(insert_pos, TransactionBehavior)
        logger.debug("TransactionBehavior registered")
