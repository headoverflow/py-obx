import contextvars as c

task: c.ContextVar[dict] = c.ContextVar('task')
