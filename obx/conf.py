import contextlib as cl
import functools as ft
import typing as t

from . import errors
from .connect import ABCConnection
from .counter import Counter


class Conf:
    _connection_type: type[ABCConnection] | None = None

    _handlers: dict[str, t.Callable[..., t.Coroutine]] = {}

    _middlewares: list[t.Callable[..., t.Coroutine]] = []

    _counter: Counter = Counter()

    _shutdown: bool = False

    def __call__(self, *_, **__):
        raise NotImplementedError

    @classmethod
    def set_connection_type(cls, connection_type: type[ABCConnection]) -> type['Conf']:
        if not issubclass(connection_type, ABCConnection):
            raise errors.ConnectionTypeUnknownObxError

        cls._connection_type = connection_type

        return cls

    @classmethod
    def get_connection_type(cls) -> type[ABCConnection]:
        if not cls._connection_type:
            raise errors.ConnectionTypeNotSetObxError

        return cls._connection_type

    @classmethod
    def set_handler(cls, name: str, fn: t.Callable[..., t.Coroutine]) -> type['Conf']:
        cls._handlers[name] = fn

        return cls

    @classmethod
    def get_handler(cls, name: str) -> t.Callable[..., t.Coroutine]:
        try:
            handler = cls._handlers[name]
        except KeyError as e:
            raise errors.TaskHandlerNotSetObxError from e

        for i in Conf._middlewares:
            handler = ft.update_wrapper(ft.partial(i, handler), handler)

        return handler

    @classmethod
    def add_middleware(cls, fn: t.Callable[..., t.Coroutine]) -> type['Conf']:
        cls._middlewares.append(fn)

        return cls

    @classmethod
    def get_counter(cls) -> Counter:
        return cls._counter

    @classmethod
    def set_shutdown(cls):
        cls._shutdown = True

    @classmethod
    def get_shutdown(cls) -> bool:
        return cls._shutdown

    @classmethod
    @cl.asynccontextmanager
    async def get_connection(cls) -> t.AsyncIterator[ABCConnection]:
        async with cls.get_connection_type()() as c:
            yield c
