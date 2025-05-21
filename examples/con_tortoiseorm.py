import tortoise

import obx


class TortoiseConnection(obx.ABCConnection):
    @classmethod
    async def acquire(cls) -> tortoise.BaseDBAsyncClient:
        return tortoise.Tortoise.get_connection('default')

    @classmethod
    async def release(cls, _):
        pass

    async def execute(self, query: str, *args) -> list[dict]:
        return (await self._connection.execute_query(query, args))[1]
