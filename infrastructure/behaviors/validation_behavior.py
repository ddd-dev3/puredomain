"""
验证 Behavior

自动验证所有 Command/Query 的输入参数：
- 使用 Pydantic 进行模型验证
- 验证失败时抛出 ValidationException
- 支持自定义验证器

执行顺序：在所有 Behavior 之前执行（pipeline 最外层）
"""

from typing import Any, Callable, Awaitable, List, Optional
from pydantic import BaseModel, ValidationError

from infrastructure.logging import get_logger
from interfaces.api.middleware.logging_middleware import get_request_id

logger = get_logger(__name__)


class ValidationException(Exception):
    """
    验证异常

    当 Command/Query 验证失败时抛出。
    包含详细的验证错误信息。
    """

    def __init__(self, errors: List[dict], request_type: str):
        self.errors = errors
        self.request_type = request_type
        self.message = f"Validation failed for {request_type}"
        super().__init__(self.message)


class ValidationBehavior:
    """
    验证 Behavior

    在 Handler 执行前自动验证请求对象。
    仅对 Pydantic BaseModel 子类进行验证。
    """

    async def handle(
        self,
        request: Any,
        next_handler: Callable[[], Awaitable[Any]]
    ) -> Any:
        """
        执行验证逻辑

        Args:
            request: Command 或 Query 对象
            next_handler: 调用下一个 behavior 或实际 handler 的函数
        """
        request_id = get_request_id() or "-"
        request_name = type(request).__name__

        # 只对 Pydantic 模型进行验证
        if isinstance(request, BaseModel):
            try:
                # 重新验证模型（捕获任何绕过初始验证的情况）
                request.model_validate(request.model_dump())
                logger.debug(f"[{request_id}] {request_name} validation passed")

            except ValidationError as e:
                errors = e.errors()
                logger.warning(
                    f"[{request_id}] {request_name} validation failed: {len(errors)} error(s)"
                )
                for error in errors:
                    logger.debug(f"[{request_id}]   - {error['loc']}: {error['msg']}")

                raise ValidationException(
                    errors=[
                        {
                            "field": ".".join(str(loc) for loc in err["loc"]),
                            "message": err["msg"],
                            "type": err["type"]
                        }
                        for err in errors
                    ],
                    request_type=request_name
                )

        # 继续执行下一个 behavior 或 handler
        return await next_handler()


def register_validation_behavior() -> None:
    """
    注册验证 Behavior 到 mediatr

    必须在应用启动时调用。
    ValidationBehavior 应该是第一个执行的 behavior（插入到位置 0）。
    """
    from typing import Any
    import mediatr

    if Any not in mediatr.__behaviors__:
        mediatr.__behaviors__[Any] = []

    # 插入到最前面，确保验证最先执行
    if ValidationBehavior not in mediatr.__behaviors__[Any]:
        mediatr.__behaviors__[Any].insert(0, ValidationBehavior)
        logger.debug("ValidationBehavior registered")
