import asyncio
import json
import logging
import traceback
import typing as t
import uuid

from . import context, errors, queries
from .conf import Conf
from .connect import ABCConnection, Transaction
from .task import State, Task

log: logging.Logger = logging.getLogger(__name__)


async def migrate():
    """Creates the schema `obx` and the table `tasks`. If the schema already
    exists then migration process will be stopped.
    """

    async with Conf.get_connection() as c, Transaction(c):
        r = await c.execute(queries.SCHEMA_EXISTS)

        if r[0]['exists']:
            return

        await c.execute(queries.EXTENSION_CREATE)

        await c.execute(queries.SCHEMA_CREATE)

        await c.execute(queries.TABLE_CREATE)

        await c.execute(queries.INDEX_CREATE_START_AFTER)

        await c.execute(queries.INDEX_CREATE_START_AT)

        await c.execute(queries.INDEX_CREATE_HANDLER_SINGLE)


async def start(delay: int = 10, active_tasks_limit: int = 10):
    """Starts tasks selecting from the tasks table every `delay` seconds.

    :param delay:
        Delay between ready for start tasks selecting.

    :param active_tasks_limit:
        How many tasks can be run at the same time.
    """

    log.info('started')

    while 1:
        await asyncio.sleep(delay)

        if Conf.get_shutdown():
            break

        log.info('select: counter=%s', Conf.get_counter().val())

        try:
            await task_update(State.timeout)

            limit = active_tasks_limit - Conf.get_counter().val()

            if limit < 1:
                log.info('active tasks limit exceeded')

                continue

            result = await select(limit)

            for i in result:
                asyncio.create_task(handle(i))
        except:  # pylint: disable=bare-except
            log.exception('select failed')

    log.info('stopped')


async def select(limit: int) -> list[dict]:
    async with Conf.get_connection() as c, Transaction(c):
        r = list(await c.execute(queries.TASK_SELECT_RUN, limit))

        if len(r) == 0:
            return []

        await c.execute(queries.TASK_UPDATE_WORK, tuple(i['id'] for i in r))

    return r


async def handle(row: dict):
    try:
        handler = Conf.get_handler(row['handler'])
    except errors.TaskHandlerNotSetObxError:
        log.exception(
            'handler not set: id=%s handler=%s',
            row['id'],
            row['handler'],
        )

        await task_update(State.fail, row['id'], 'handler not set')

        return

    context.task.set(row)

    log.info('task starting: id=%s handler=%s', row['id'], row['handler'])

    params = row['params']

    if isinstance(params, str):  # orm specific behavior fix
        params = json.loads(row['params'])

    await Conf.get_counter().inc()

    try:
        await handler(**params)
    except:  # pylint: disable=bare-except
        log.exception('task fail: id=%s handler=%s', row['id'], row['handler'])

        await task_update(State.fail, row['id'], traceback.format_exc())
    else:
        log.info('task done: id=%s handler=%s', row['id'], row['handler'])

        await task_update(State.done, row['id'])
    finally:
        await Conf.get_counter().dec()


async def task_insert(connection: t.Any, task: Task):
    """Inserts the task into the `obx.tasks` table.

    :param connection:
        Database connection.

    :param task:
        Configured task.
    """

    if not isinstance(connection, ABCConnection):
        connection = Conf.get_connection_type()(connection)

    await connection.execute(queries.TASK_INSERT, *task.build())


async def task_update(
    target_state: State,
    pk: uuid.UUID | None = None,
    error: str | None = None,
):
    """Updates one task when state parameter equals `done` or `fail` and updates
    several tasks when state parameter equals `timeout`.

    :param target_state:
        Target state of the working task you need to update.

    :param pk:
        ID of the task you need to update.
        If the `target_state` equals `timeout` then the parameter `pk` will
        be ignored because in this case all tasks working over expected time
        will be updated.

    :param error:
        Error message that will be used when the `target_state` equals `fail`.
        Will be ignored if the `target_state` equals `done` or `timeout`.
    """

    async with Conf.get_connection() as c:
        match target_state:
            case State.done:
                await c.execute(queries.TASK_UPDATE_DONE, pk)
            case State.fail:
                await c.execute(queries.TASK_UPDATE_FAIL, pk, error)
            case State.timeout:
                await c.execute(queries.TASK_UPDATE_TIMEOUT)
            case _:
                raise errors.TaskStateUnknownObxError
