import pytest

from obx.counter import Counter


async def test__counter():
    c = Counter()

    assert 1 == await c.inc()

    assert 2 == await c.inc()

    assert 1 == await c.dec()

    assert 0 == await c.dec()

    with pytest.raises(ValueError):
        await c.dec()
