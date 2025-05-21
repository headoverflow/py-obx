import asyncpg

from obx import errors
from obx.connect import ABCConnection


class PooledConnection(ABCConnection):
    _pool: asyncpg.Pool | None = None

    @classmethod
    def set_pool(cls, pool: asyncpg.Pool):
        cls._pool = pool

    @classmethod
    async def acquire(cls) -> asyncpg.Connection:
        if not cls._pool:
            raise errors.PoolNotSetObxError

        return await cls._pool.acquire()

    @classmethod
    async def release(cls, connection: asyncpg.Connection):
        if not cls._pool:
            raise errors.PoolNotSetObxError

        await cls._pool.release(connection)

    async def execute(self, query: str, *args, **kwargs) -> list[dict]:
        if not self._connection:
            raise errors.ConnectionNotSetObxError

        return await self._connection.fetch(query, *args, **kwargs)
