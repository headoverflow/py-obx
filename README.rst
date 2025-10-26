PyObx
=====

Outbox pattern realization for `asyncpg <https://github.com/MagicStack/asyncpg>`_ based apps.
Stores records in ``obx.tasks`` table.


Installation
------------

Use pip to install::

    $ pip install git+https://github.com/headoverflow/py-obx


Basic Usage
-----------

Before run the code below, make sure you have installed `asyncpg <https://github.com/MagicStack/asyncpg>`_.

.. code-block:: python

    import asyncio
    import typing as t

    import asyncpg

    import obx


    async def main():
        pool = await asyncpg.create_pool('postgres://postgres:postgres@localhost:5432/postgres')

        obx.PooledConnection.set_pool(pool)

        (
            obx.Conf
            .set_connection_type(obx.PooledConnection)
            .set_handler('foo', foo)
            .add_middleware(mw)
        )

        await obx.migrate()

        asyncio.create_task(obx.start())

        async with pool.acquire() as c:
            await c.execute('BEGIN')

            try:
                await obx.task_insert(c, obx.Task('foo').set_params(n=2))
            except:
                await c.execute('ROLLBACK')
            else:
                await c.execute('COMMIT')

        await asyncio.sleep(20)  # waiting for task finished

        obx.Conf.set_shutdown()


    async def mw(fn: t.Callable[..., t.Coroutine], *args, **kwargs):
        print('before')

        try:
            await fn(*args, **kwargs)
        finally:
            print('after')


    async def foo(n: int = 1, msg: str = 'bar'):
        for _ in range(n):
            print(msg)


    asyncio.run(main())

You can implement your own database connection class using examples:

* `SQLAlchemy (~=2.0.0) <https://github.com/headoverflow/py-obx/blob/master/examples/con_sqlalchemy.py>`_ (use autocommit mode)
* `Tortoise ORM (~=0.24.0) <https://github.com/headoverflow/py-obx/blob/master/examples/con_tortoiseorm.py>`_
