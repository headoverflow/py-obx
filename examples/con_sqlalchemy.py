import sqlalchemy.ext.asyncio as sa

import obx


class SAConnection(obx.ABCConnection):
    _engine: sa.AsyncEngine | None = None

    @classmethod
    def set_engine(cls, engine: sa.AsyncEngine):
        cls._engine = engine

    @classmethod
    async def acquire(cls) -> sa.AsyncConnection:
        if not cls._engine:
            raise ValueError

        return await cls._engine.connect()

    @classmethod
    async def release(cls, connection: sa.AsyncConnection):
        await connection.close()

    async def execute(self, query: str, *args) -> list[dict]:
        cursor = await self._connection.exec_driver_sql(query, args)

        try:
            if not cursor.returns_rows:
                return []

            return list(cursor.mappings())
        finally:
            cursor.close()
