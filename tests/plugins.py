import collections as cl
import datetime as dt
import typing as t

import asyncpg
import pytest


@pytest.fixture
async def db() -> t.AsyncIterator[asyncpg.Connection]:
    c = await asyncpg.connect('postgres://postgres:postgres@localhost:5432/test')

    try:
        yield c
    finally:
        await c.close()


@pytest.fixture
def fct_task(db) -> t.Callable[..., t.Coroutine]:
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    async def w(
        handler: str | None = None,
        params: dict | None = None,
        single: bool | None = None,
        start_after: dt.datetime | None = None,
        start_at: dt.datetime | None = None,
        done_at: dt.datetime | None = None,
        fail_at: dt.datetime | None = None,
        error: str | None = None,
        delta_done: dt.timedelta | None = None,
        delta_fail: dt.timedelta | None = None,
        delta_timeout: dt.timedelta | None = None,
    ) -> tuple:
        r = await db.fetchrow(
            (
                'INSERT INTO obx.tasks '
                '(handler, params, single, start_after, '
                'start_at, done_at, fail_at, error, '
                'delta_done, delta_fail, delta_timeout) '
                'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) '
                'RETURNING *'
            ),
            handler or 'test',
            params or '{}',
            single or False,
            start_after or dt.datetime.now(),
            start_at or None,
            done_at or None,
            fail_at or None,
            error or '',
            delta_done,
            delta_fail,
            delta_timeout,
        )

        return cl.namedtuple('Task', r.keys())(**r)

    return w
