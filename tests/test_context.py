import typing as t

from obx.context import Context


async def test__add_middleware():
    i = 0

    async def fn():
        nonlocal i

        i += 1

        raise ValueError

    Context.set_handler('fn', fn)

    async def mw(fn: t.Callable[..., t.Coroutine], *args, **kwargs):
        try:
            await fn(*args, **kwargs)
        finally:
            nonlocal i

            i += 1

    Context.add_middleware(mw)

    try:
        await Context.get_handler('fn')()
    except ValueError:
        pass

    assert i == 2
