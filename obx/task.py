import datetime as dt
import enum
import json
import typing as t
import uuid

from . import errors

State = enum.Enum('State', 'done fail timeout')


class Task:
    # pylint: disable=too-many-instance-attributes

    def __init__(self, handler: str):
        self._id: uuid.UUID = uuid.uuid4()

        self._handler: str = handler

        self._params: dict[str, t.Any] = {}

        self._single: bool = False

        self._start_after: dt.datetime = dt.datetime.now(dt.timezone.utc)

        self._error: str = ''

        self._delta_done: dt.timedelta | None = None

        self._delta_fail: dt.timedelta | None = None

        self._delta_timeout: dt.timedelta = dt.timedelta(minutes=10)

    def set_id(self, pk: uuid.UUID) -> 'Task':
        self._id = pk

        return self

    def set_params(self, **value) -> 'Task':
        self._params = value

        return self

    def set_single(self) -> 'Task':
        self._single = True

        return self

    def set_start_after(self, t: dt.datetime) -> 'Task':
        self._start_after = t

        return self

    def set_start_after_delta(self, *, d: int = 0, h: int = 0, m: int = 0, s: int = 0) -> 'Task':
        self._start_after += dt.timedelta(
            days=d,
            hours=h,
            minutes=m,
            seconds=s,
        )

        return self

    def set_delta_done(self, *, d: int = 0, h: int = 0, m: int = 0, s: int = 0) -> 'Task':
        self._delta_done = dt.timedelta(
            days=d,
            hours=h,
            minutes=m,
            seconds=s,
        )

        return self

    def set_delta_fail(self, *, d: int = 0, h: int = 0, m: int = 0, s: int = 0) -> 'Task':
        self._delta_fail = dt.timedelta(
            days=d,
            hours=h,
            minutes=m,
            seconds=s,
        )

        return self

    def set_delta_timeout(self, *, d: int = 0, h: int = 0, m: int = 0, s: int = 0) -> 'Task':
        self._delta_timeout = dt.timedelta(
            days=d,
            hours=h,
            minutes=m,
            seconds=s,
        )

        return self

    def build(self) -> tuple:
        if not self._handler:
            raise errors.TaskHandlerNotSetObxError

        return (
            self._id,
            self._handler,
            json.dumps(self._params),
            self._single,
            self._start_after,
            self._error,
            self._delta_done,
            self._delta_fail,
            self._delta_timeout,
        )
