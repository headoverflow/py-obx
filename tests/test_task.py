import datetime as dt
import unittest.mock
import uuid

from obx.task import Task


def test__build_default():
    t = Task('foo').build()

    assert t == (
        unittest.mock.ANY,
        'foo',
        '{}',
        False,
        unittest.mock.ANY,
        '',
        None,
        None,
        dt.timedelta(minutes=10),
    )

    assert t[4]


def test__build_parameterized():
    u = uuid.uuid4()

    t = (
        Task('foo')
        .set_id(u)
        .set_params(foo='bar')
        .set_single()
        .set_start_after_delta(m=1)
        .set_delta_done(m=2)
        .set_delta_fail(m=4)
        .set_delta_timeout(m=8)
        .build()
    )

    assert t == (
        u,
        'foo',
        '{"foo": "bar"}',
        True,
        unittest.mock.ANY,
        unittest.mock.ANY,
        dt.timedelta(minutes=2),
        dt.timedelta(minutes=4),
        dt.timedelta(minutes=8),
    )

    assert t[4] - dt.datetime.now(dt.timezone.utc) < dt.timedelta(minutes=1)
