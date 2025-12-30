"""
API 接口层

提供 FastAPI + FastMCP 集成，支持 REST API 和 MCP 工具。

用法：
    from interfaces.api import App

    app = App("MyService")

    @app.get("/users")
    async def list_users():
        return []

    @app.mcp_tool
    async def get_user(user_id: int) -> dict:
        '''获取用户'''
        return {}

    app.run()

异常处理：
    框架自动注册异常处理器，将 ApplicationException 和 ValidationException
    转换为统一的 JSON 响应格式。
"""

from interfaces.api.app import App, create_app
from interfaces.api.exception_handlers import register_exception_handlers

__all__ = [
    "App",
    "create_app",
    "register_exception_handlers",
]
