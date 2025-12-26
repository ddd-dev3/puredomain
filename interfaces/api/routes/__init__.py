"""
REST API 路由

定义 REST API 端点。

使用示例：
    from interfaces.api.routes import health_router

    # 在 FastAPI 应用中注册
    app.include_router(health_router)

添加新路由：
    1. 在 routes/ 下创建新文件，如 users.py
    2. 定义 router = APIRouter(prefix="/users", tags=["Users"])
    3. 在此文件中导入并导出
"""

from interfaces.api.routes.health import router as health_router

__all__ = ["health_router"]
