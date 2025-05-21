import asyncio


class Counter:
    def __init__(self):
        self._lock = asyncio.Lock()

        self._value = 0

    async def __aenter__(self):
        await self._lock.acquire()

    async def __aexit__(self, *_, **__):
        self._lock.release()

    def val(self) -> int:
        return self._value

    async def inc(self) -> int:
        async with self:
            self._value += 1

        return self._value

    async def dec(self) -> int:
        async with self:
            self._value -= 1

        if self._value < 0:
            raise ValueError

        return self._value
