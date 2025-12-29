"""
HTTP 请求日志中间件

自动记录每个 HTTP 请求的：
- 请求方法和路径
- 响应状态码
- 请求耗时
- 请求 ID（用于链路追踪）
"""

import time
from uuid import uuid4
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from infrastructure.logging import get_logger

logger = get_logger(__name__)

# 请求 ID 上下文变量（可在整个请求链路中访问）
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """获取当前请求 ID"""
    return request_id_var.get()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP 请求日志中间件

    自动记录请求开始和结束，包含耗时统计。
    生成唯一请求 ID 用于链路追踪。
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # 生成请求 ID
        request_id = uuid4().hex[:8]
        request_id_var.set(request_id)

        # 记录请求开始
        method = request.method
        path = request.url.path
        logger.info(f"[{request_id}] -> {method} {path}")

        # 计时
        start = time.perf_counter()

        try:
            response = await call_next(request)

            # 记录请求结束
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                f"[{request_id}] <- {response.status_code} {duration_ms:.0f}ms"
            )

            return response

        except Exception as e:
            # 记录异常
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(f"[{request_id}] <- ERROR {type(e).__name__}: {e} {duration_ms:.0f}ms")
            raise
