import abc
import typing as t


class ABCConnection(abc.ABC):
    def __init__(self, raw_connection: t.Any = None):
        self._connection: t.Any = raw_connection

        self._is_borrowed: bool = self._connection is not None

    async def __aenter__(self) -> 'ABCConnection':
        if not self._is_borrowed:
            self._connection = await self.acquire()

        return self

    async def __aexit__(self, *_):
        if not self._is_borrowed:
            await self.release(self._connection)

            self._connection = None

    @classmethod
    @abc.abstractmethod
    async def acquire(cls) -> t.Any:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    async def release(cls, connection: t.Any):
        raise NotImplementedError

    @abc.abstractmethod
    async def execute(self, query: str, *_) -> list[dict]:
        raise NotImplementedError


class Transaction:
    def __init__(self, connection: ABCConnection):
        self._connection: ABCConnection = connection

    async def __aenter__(self):
        await self._connection.execute('BEGIN')

    async def __aexit__(self, tp: t.Type[Exception] | None, *_):
        if tp:
            await self._connection.execute('ROLLBACK')
        else:
            await self._connection.execute('COMMIT')

    async def execute(self, query: str, *args, **kwargs) -> list[dict]:
        return await self._connection.execute(query, *args, **kwargs)
