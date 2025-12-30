"""
Repository 层日志 Mixin

自动记录所有 Repository 的 CRUD 操作：
- add: 添加实体
- get_by_id: 查询实体
- remove: 删除实体
- list: 列表查询

日志包含 request_id 用于链路追踪。

使用方式：
    class UserRepository(LoggingRepositoryMixin, SqlAlchemyRepository):
        pass  # 自动有日志
"""

from typing import Any, Optional, List, TypeVar
from functools import cached_property

from infrastructure.logging import get_logger
from interfaces.api.middleware.logging_middleware import get_request_id

TEntity = TypeVar("TEntity")
TId = TypeVar("TId")


class LoggingRepositoryMixin:
    """
    Repository 日志混入

    为 Repository 实现提供自动日志记录能力。
    继承时放在第一位（MRO 顺序）。

    日志级别为 DEBUG，生产环境可通过配置关闭。
    """

    @cached_property
    def _repo_logger(self):
        """获取 logger（使用类名作为 logger 名称）"""
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def _log_prefix(self) -> str:
        """获取日志前缀（包含 request_id）"""
        request_id = get_request_id() or "-"
        return f"[{request_id}]"

    async def add(self, entity: TEntity) -> None:
        """添加实体（带日志）"""
        prefix = self._log_prefix()
        entity_name = type(entity).__name__
        entity_id = getattr(entity, "id", "?")
        self._repo_logger.debug(f"{prefix} add({entity_name}[{entity_id}])")

        result = await super().add(entity)

        self._repo_logger.debug(f"{prefix} add({entity_name}[{entity_id}]) -> done")
        return result

    async def get_by_id(self, entity_id: TId) -> Optional[TEntity]:
        """根据 ID 获取实体（带日志）"""
        prefix = self._log_prefix()
        self._repo_logger.debug(f"{prefix} get_by_id({entity_id})")

        result = await super().get_by_id(entity_id)

        if result:
            self._repo_logger.debug(f"{prefix} get_by_id({entity_id}) -> found")
        else:
            self._repo_logger.debug(f"{prefix} get_by_id({entity_id}) -> not found")

        return result

    async def remove(self, entity: TEntity) -> None:
        """移除实体（带日志）"""
        prefix = self._log_prefix()
        entity_name = type(entity).__name__
        entity_id = getattr(entity, "id", "?")
        self._repo_logger.debug(f"{prefix} remove({entity_name}[{entity_id}])")

        result = await super().remove(entity)

        self._repo_logger.debug(f"{prefix} remove({entity_name}[{entity_id}]) -> done")
        return result

    async def list(self, specification: Optional[Any] = None) -> List[TEntity]:
        """列表查询（带日志）"""
        prefix = self._log_prefix()
        spec_name = type(specification).__name__ if specification else "None"
        self._repo_logger.debug(f"{prefix} list(spec={spec_name})")

        result = await super().list(specification)

        self._repo_logger.debug(f"{prefix} list(spec={spec_name}) -> {len(result)} items")
        return result
