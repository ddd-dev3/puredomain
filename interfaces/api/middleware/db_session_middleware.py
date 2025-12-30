"""
数据库 Session 管理中间件

在每个请求开始时创建 Session，结束时关闭并归还到连接池。
解决连接池耗尽问题。
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import sessionmaker

from infrastructure.containers.infrastructure import set_request_session
from infrastructure.logging import get_logger

logger = get_logger(__name__)


class DBSessionMiddleware(BaseHTTPMiddleware):
    """
    数据库 Session 中间件

    为每个 HTTP 请求创建独立的 Session，并在请求结束时关闭。
    Session 通过 contextvars 存储，可以被 Repository 访问。
    """

    def __init__(self, app, session_factory: sessionmaker):
        super().__init__(app)
        self._session_factory = session_factory

    async def dispatch(self, request: Request, call_next) -> Response:
        # 创建新的 Session
        session = self._session_factory()

        # 设置到 contextvar（Repository 可以访问）
        set_request_session(session)

        try:
            response = await call_next(request)
            # 成功时提交事务（如果有待提交的更改）
            await session.commit()
            return response
        except Exception as e:
            # 发生异常时回滚
            await session.rollback()
            raise
        finally:
            # 清理：关闭 Session，归还连接到连接池
            set_request_session(None)
            await session.close()
