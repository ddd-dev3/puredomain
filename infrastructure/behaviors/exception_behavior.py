"""
异常处理 Behavior

统一处理 Handler 执行过程中的异常：
- 将领域异常（DomainException）转换为应用层异常
- 记录详细的异常日志（包含 request_id）
- 提供统一的异常响应格式

执行顺序：在 ValidationBehavior 之后，LoggingBehavior 之前
"""

from typing import Any, Callable, Awaitable, Dict, Type
from dataclasses import dataclass

from domain.common.exceptions import (
    DomainException,
    EntityNotFoundException,
    AggregateNotFoundException,
    BusinessRuleViolationException,
    DomainValidationException,
    InvalidOperationException,
    DuplicateEntityException,
    AggregateVersionMismatchException,
    AuthenticationException,
)
from infrastructure.logging import get_logger
from interfaces.api.middleware.logging_middleware import get_request_id

logger = get_logger(__name__)


@dataclass
class ApplicationError:
    """
    应用层错误

    统一的错误响应格式，可被 API 层转换为 HTTP 响应。
    """
    code: str
    message: str
    status_code: int
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ApplicationException(Exception):
    """
    应用层异常

    携带 ApplicationError 信息，供 API 层处理。
    """

    def __init__(self, error: ApplicationError):
        self.error = error
        super().__init__(error.message)


# 领域异常 -> HTTP 状态码映射
EXCEPTION_STATUS_MAP: Dict[Type[DomainException], int] = {
    EntityNotFoundException: 404,
    AggregateNotFoundException: 404,
    BusinessRuleViolationException: 422,
    DomainValidationException: 400,
    InvalidOperationException: 400,
    DuplicateEntityException: 409,
    AggregateVersionMismatchException: 409,
    AuthenticationException: 401,
}


class ExceptionBehavior:
    """
    异常处理 Behavior

    捕获 Handler 中的异常并转换为统一格式。
    """

    async def handle(
        self,
        request: Any,
        next_handler: Callable[[], Awaitable[Any]]
    ) -> Any:
        """
        执行异常处理逻辑

        Args:
            request: Command 或 Query 对象
            next_handler: 调用下一个 behavior 或实际 handler 的函数
        """
        request_id = get_request_id() or "-"
        request_name = type(request).__name__

        try:
            return await next_handler()

        except ApplicationException:
            # 已经是应用层异常，直接抛出
            raise

        except DomainException as e:
            # 领域异常 -> 应用层异常
            status_code = self._get_status_code(e)

            logger.warning(
                f"[{request_id}] {request_name} domain exception: "
                f"{e.code} - {e.message}"
            )

            raise ApplicationException(
                ApplicationError(
                    code=e.code,
                    message=e.message,
                    status_code=status_code,
                    details=self._extract_details(e)
                )
            )

        except Exception as e:
            # 未预期的异常 -> 500 内部错误
            logger.error(
                f"[{request_id}] {request_name} unexpected exception: "
                f"{type(e).__name__}: {e}",
                exc_info=True
            )

            raise ApplicationException(
                ApplicationError(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred",
                    status_code=500,
                    details={"exception_type": type(e).__name__}
                )
            )

    def _get_status_code(self, exception: DomainException) -> int:
        """获取异常对应的 HTTP 状态码"""
        for exc_type, status_code in EXCEPTION_STATUS_MAP.items():
            if isinstance(exception, exc_type):
                return status_code
        return 400  # 默认 Bad Request

    def _extract_details(self, exception: DomainException) -> Dict[str, Any]:
        """提取异常的详细信息"""
        details = {}

        # 提取异常的自定义属性
        for attr in dir(exception):
            if not attr.startswith("_") and attr not in ("message", "code", "args"):
                value = getattr(exception, attr, None)
                if value is not None and not callable(value):
                    details[attr] = str(value)

        return details


def register_exception_behavior() -> None:
    """
    注册异常处理 Behavior 到 mediatr

    必须在应用启动时调用。
    ExceptionBehavior 应该在 ValidationBehavior 之后执行。
    """
    from typing import Any
    import mediatr

    if Any not in mediatr.__behaviors__:
        mediatr.__behaviors__[Any] = []

    # 插入到位置 1（在 ValidationBehavior 之后）
    if ExceptionBehavior not in mediatr.__behaviors__[Any]:
        # 找到合适的位置插入
        insert_pos = 1 if len(mediatr.__behaviors__[Any]) > 0 else 0
        mediatr.__behaviors__[Any].insert(insert_pos, ExceptionBehavior)
        logger.debug("ExceptionBehavior registered")
