import typing as t

from obx.conf import Conf


async def test__add_middleware():
    i = 0

    async def fn():
        nonlocal i

        i += 1

        raise ValueError

    Conf.set_handler('fn', fn)

    async def mw(fn: t.Callable[..., t.Coroutine], *args, **kwargs):
        try:
            await fn(*args, **kwargs)
        finally:
            nonlocal i

            i += 1

    Conf.add_middleware(mw)

    try:
        await Conf.get_handler('fn')()
    except ValueError:
        pass

    assert i == 2
