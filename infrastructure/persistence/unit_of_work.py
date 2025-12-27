"""
工作单元模式实现（Unit of Work）- 异步版

用于管理事务边界和数据库会话生命周期

基于 SQLAlchemy AsyncSession 实现。
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager


class UnitOfWork:
    """
    异步工作单元 - AsyncSession 实现

    用法：
        async with UnitOfWork(session_factory) as uow:
            # 执行业务逻辑
            user = User(name="test")
            uow.session.add(user)
            await uow.commit()  # 提交事务
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """
        初始化工作单元

        Args:
            session_factory: 返回 AsyncSession 的工厂
        """
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self):
        """进入异步上下文管理器"""
        self._session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出异步上下文管理器"""
        if exc_type is not None:
            # 发生异常，回滚
            await self.rollback()

        # 关闭 session
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> AsyncSession:
        """获取当前 Session"""
        if self._session is None:
            raise RuntimeError("UnitOfWork not started. Use 'async with UnitOfWork() as uow'")
        return self._session

    async def commit(self):
        """提交事务"""
        if self._session:
            await self._session.commit()

    async def rollback(self):
        """回滚事务"""
        if self._session:
            await self._session.rollback()

    async def flush(self):
        """刷新到数据库（不提交）"""
        if self._session:
            await self._session.flush()

    async def refresh(self, instance):
        """刷新对象状态"""
        if self._session:
            await self._session.refresh(instance)


@asynccontextmanager
async def unit_of_work(session_factory: async_sessionmaker[AsyncSession]):
    """
    工作单元异步上下文管理器（函数式）

    用法：
        async with unit_of_work(session_factory) as session:
            user = User(name="test")
            session.add(user)
            # 自动提交
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
