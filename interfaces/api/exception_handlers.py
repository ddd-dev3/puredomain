"""
API 异常处理器

将应用层异常转换为统一的 HTTP 响应格式。

响应格式：
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": {...}
    }
}
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from infrastructure.behaviors import (
    ApplicationException,
    ValidationException,
)
from infrastructure.logging import get_logger
from interfaces.api.middleware.logging_middleware import get_request_id

logger = get_logger(__name__)


async def application_exception_handler(
    request: Request,
    exc: ApplicationException
) -> JSONResponse:
    """
    处理应用层异常

    将 ApplicationException 转换为 JSON 响应。
    """
    request_id = get_request_id() or "-"
    error = exc.error

    logger.info(
        f"[{request_id}] ApplicationException: {error.code} - {error.message}"
    )

    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
                "request_id": request_id,
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: ValidationException
) -> JSONResponse:
    """
    处理验证异常

    将 ValidationException 转换为 JSON 响应。
    """
    request_id = get_request_id() or "-"

    logger.info(
        f"[{request_id}] ValidationException: {exc.request_type} - "
        f"{len(exc.errors)} error(s)"
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "details": {
                    "errors": exc.errors,
                },
                "request_id": request_id,
            }
        }
    )


async def pydantic_validation_exception_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """
    处理 Pydantic 验证异常

    将 Pydantic ValidationError 转换为 JSON 响应。
    主要用于捕获 FastAPI 路由参数验证失败的情况。
    """
    request_id = get_request_id() or "-"

    errors = [
        {
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"]
        }
        for err in exc.errors()
    ]

    logger.info(
        f"[{request_id}] Pydantic ValidationError: {len(errors)} error(s)"
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": errors,
                },
                "request_id": request_id,
            }
        }
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    注册所有异常处理器

    Args:
        app: FastAPI 应用实例
    """
    app.add_exception_handler(ApplicationException, application_exception_handler)
    app.add_exception_handler(ValidationException, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)

    logger.debug("Exception handlers registered")
