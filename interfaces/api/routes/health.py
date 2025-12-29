"""
健康检查路由

提供服务健康状态检查，用于：
- 负载均衡器健康探测
- Kubernetes liveness/readiness 探针
- 监控系统
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from infrastructure.containers.bootstrap import get_bootstrap
from infrastructure.config.settings import Settings


router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    environment: str
    timestamp: datetime
    database: Optional[str] = None


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    基础健康检查

    返回服务状态、版本和环境信息。
    """
    boot = get_bootstrap()
    settings = boot.infra.settings()

    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.app_env,
        timestamp=datetime.now(),
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """
    就绪检查（包含数据库连接）

    检查服务是否准备好接收请求。
    用于 Kubernetes readiness probe。
    """
    boot = get_bootstrap()
    settings = boot.infra.settings()

    # 检查数据库连接
    db_status = "unknown"
    try:
        session_factory = boot.infra.db_session_factory()
        session = session_factory()
        session.execute("SELECT 1")
        session.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        version="1.0.0",
        environment=settings.app_env,
        timestamp=datetime.now(),
        database=db_status,
    )
