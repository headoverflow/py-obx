import asyncio

import asyncpg
import pytest

import obx

pytest_plugins = ('tests.plugins',)


@pytest.fixture
def event_loop():
    yield asyncio.get_event_loop()


@pytest.fixture(scope='session', autouse=True)
async def init():
    con = await asyncpg.connect('postgres://postgres:postgres@localhost:5432/postgres')

    await con.execute('DROP DATABASE IF EXISTS "test"')

    await con.execute('CREATE DATABASE "test"')

    pool = await asyncpg.create_pool('postgres://postgres:postgres@localhost:5432/test')

    obx.PooledConnection.set_pool(pool)

    obx.Context.set_connection_type(obx.PooledConnection)

    await obx.migrate()

    yield

    await con.execute((
        'SELECT pg_terminate_backend(pid) '
        'FROM pg_stat_activity '
        'WHERE pid <> pg_backend_pid() AND datname = \'test\''
    ))

    await con.execute('DROP DATABASE "test"')

    await con.close()


@pytest.fixture(autouse=True)
async def clear(db):
    yield

    await db.execute('TRUNCATE obx.tasks')
