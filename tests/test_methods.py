import asyncio
import datetime as dt
import unittest.mock
import uuid

import asyncpg
import pytest

from obx import methods
from obx.connect import Transaction
from obx.context import Context
from obx.task import State, Task


async def test__start(db, fct_task):
    await fct_task()

    asyncio.create_task(methods.start(1))

    await asyncio.sleep(2)

    Context.set_shutdown()

    await asyncio.sleep(2)

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['error'] == 'handler not set'


async def test__select(db, fct_task):
    t1 = await fct_task()

    await fct_task(start_after=dt.datetime.now() + dt.timedelta(1))

    await fct_task(start_at=dt.datetime.now())

    r = await methods.select(10)

    assert len(r) == 1

    assert r[0]['id'] == t1.id

    r = await db.fetchrow('SELECT * FROM obx.tasks ORDER BY created_at LIMIT 1')

    assert r['start_at']

    assert not r['done_at']

    assert not r['fail_at']


async def test__handle(db, fct_task):
    t = await fct_task()

    async def test():
        pass

    Context.set_handler(t.handler, test)

    await methods.handle(t._asdict())

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert not r['start_at']

    assert r['done_at']

    assert not r['fail_at']


async def test__task_insert(db):
    u = uuid.uuid4()

    async with Context.get_connection() as c, Transaction(c):
        await methods.task_insert(c, Task('foo'))

        await methods.task_insert(
            c,
            (
                Task('foo')
                .set_id(u)
                .set_params(foo='bar')
                .set_single()
                .set_start_after_delta(m=1)
                .set_delta_done(d=2, m=2)
                .set_delta_fail(d=4, m=4)
                .set_delta_timeout(m=8)
            ),
        )

    r = await db.fetch('SELECT * FROM obx.tasks ORDER BY created_at')

    assert dict(r[0]) == {
        'id': unittest.mock.ANY,
        'created_at': unittest.mock.ANY,
        'updated_at': unittest.mock.ANY,
        'handler': 'foo',
        'params': '{}',
        'single': False,
        'start_after': unittest.mock.ANY,
        'start_at': None,
        'done_at': None,
        'fail_at': None,
        'error': '',
        'delta_done': None,
        'delta_fail': None,
        'delta_timeout': dt.timedelta(minutes=10),
    }

    assert dict(r[1]) == {
        'id': u,
        'created_at': unittest.mock.ANY,
        'updated_at': unittest.mock.ANY,
        'handler': 'foo',
        'params': '{"foo": "bar"}',
        'single': True,
        'start_after': unittest.mock.ANY,
        'start_at': None,
        'done_at': None,
        'fail_at': None,
        'error': '',
        'delta_done': dt.timedelta(days=2, minutes=2),
        'delta_fail': dt.timedelta(days=4, minutes=4),
        'delta_timeout': dt.timedelta(minutes=8),
    }

    assert dt.timedelta(minutes=1) > \
        r[1]['start_after'] - dt.datetime.now(dt.timezone.utc)


async def test__task_insert__single(fct_task):
    await fct_task(handler='foo', single=True)

    with pytest.raises(asyncpg.UniqueViolationError):
        async with Context.get_connection() as c, Transaction(c):
            await methods.task_insert(c, Task('foo').set_single())


async def test__task_update__done(db, fct_task):
    t = await fct_task(
        start_after=dt.datetime.now(),
        start_at=dt.datetime.now(),
    )

    await methods.task_update(State.done, t.id)

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['start_at'] == t.start_at

    assert r['done_at']

    assert not r['fail_at']


async def test__task_update__done_delta(db, fct_task):
    t = await fct_task(
        start_after=dt.datetime.now(),
        start_at=dt.datetime.now(),
        delta_done=dt.timedelta(1),
    )

    await methods.task_update(State.done, t.id)

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['start_after'] == t.start_after + t.delta_done

    assert not r['start_at']

    assert not r['done_at']

    assert not r['fail_at']


async def test__task_update__done_delta_2(db, fct_task):
    t = await fct_task(
        start_after=dt.datetime(1970, 1, 1),
        start_at=dt.datetime.now(),
        delta_done=dt.timedelta(1),
    )

    await methods.task_update(State.done, t.id)

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['start_after'] > dt.datetime.now(dt.timezone.utc)


async def test__task_update__fail(db, fct_task):
    t = await fct_task(
        start_after=dt.datetime.now(),
        start_at=dt.datetime.now(),
    )

    await methods.task_update(State.fail, t.id, 'test')

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['start_at'] == t.start_at

    assert not r['done_at']

    assert r['fail_at']

    assert r['error'] == 'test'


async def test__task_update__fail_delta(db, fct_task):
    t = await fct_task(
        start_after=dt.datetime.now(),
        start_at=dt.datetime.now(),
        delta_fail=dt.timedelta(1),
    )

    await methods.task_update(State.fail, t.id, 'test')

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['start_after'] == t.start_after + t.delta_fail

    assert not r['start_at']

    assert not r['done_at']

    assert not r['fail_at']

    assert r['error'] == 'test'


async def test__task_update__fail_delta_2(db, fct_task):
    t = await fct_task(
        start_after=dt.datetime(1970, 1, 1),
        start_at=dt.datetime.now(),
        delta_fail=dt.timedelta(1),
    )

    await methods.task_update(State.fail, t.id, 'test')

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['start_after'] > dt.datetime.now(dt.timezone.utc)


async def test__task_update__timeout(db, fct_task):
    t = await fct_task(
        start_after=dt.datetime.now(),
        start_at=dt.datetime.now(),
        delta_timeout=dt.timedelta(),
    )

    await methods.task_update(State.timeout)

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['start_at'] == t.start_at

    assert not r['done_at']

    assert r['fail_at']

    assert r['error'] == 'timeout'


async def test__task_update__timeout_delta(db, fct_task):
    t = await fct_task(
        start_after=dt.datetime.now(),
        start_at=dt.datetime.now(),
        delta_fail=dt.timedelta(1),
        delta_timeout=dt.timedelta(),
    )

    await methods.task_update(State.timeout)

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['start_after'] == t.start_after + t.delta_fail

    assert not r['start_at']

    assert not r['done_at']

    assert not r['fail_at']

    assert r['error'] == 'timeout'


async def test__task_update__timeout_delta_2(db, fct_task):
    await fct_task(
        start_after=dt.datetime(1970, 1, 1),
        start_at=dt.datetime.now(),
        delta_fail=dt.timedelta(1),
        delta_timeout=dt.timedelta(),
    )

    await methods.task_update(State.timeout)

    r = await db.fetchrow('SELECT * FROM obx.tasks')

    assert r['start_after'] > dt.datetime.now(dt.timezone.utc)
