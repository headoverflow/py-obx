def _(*args) -> str:
    return '\n'.join(args)


SCHEMA_EXISTS = _(
    'SELECT exists(',
    '  SELECT 1',
    '  FROM information_schema.schemata',
    '  WHERE schema_name = \'obx\'',
    ')',
)

EXTENSION_CREATE = 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'

SCHEMA_CREATE = 'CREATE SCHEMA obx'

TABLE_CREATE = _(
    'CREATE TABLE obx.tasks (',
    '  id            UUID        NOT NULL DEFAULT uuid_generate_v4(),',
    '  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),',
    '  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),',
    '  handler       TEXT        NOT NULL,',
    '  params        JSONB       NOT NULL,',
    '  single        BOOL        NOT NULL DEFAULT FALSE,',
    '  start_after   TIMESTAMPTZ NOT NULL,',
    '  start_at      TIMESTAMPTZ,',
    '  done_at       TIMESTAMPTZ,',
    '  fail_at       TIMESTAMPTZ,',
    '  error         TEXT        NOT NULL DEFAULT \'\',',
    '  delta_done    INTERVAL,',
    '  delta_fail    INTERVAL,',
    '  delta_timeout INTERVAL,',
    '',
    '  PRIMARY KEY (id)',
    ')',
)

INDEX_CREATE_START_AFTER = 'CREATE INDEX ON obx.tasks (start_after)'

INDEX_CREATE_START_AT = 'CREATE INDEX ON obx.tasks (start_at)'

INDEX_CREATE_HANDLER_SINGLE = 'CREATE UNIQUE INDEX ON obx.tasks (handler, single) WHERE single'

TASK_INSERT = _(
    'INSERT INTO obx.tasks (',
    '  id,',
    '  handler,',
    '  params,',
    '  single,',
    '  start_after,',
    '  error,',
    '  delta_done,',
    '  delta_fail,',
    '  delta_timeout',
    ')',
    'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)',
    'RETURNING id',
)

TASK_SELECT_RUN = _(
    'SELECT *',
    'FROM obx.tasks',
    'WHERE start_after AT TIME ZONE \'utc\' < now() AT TIME ZONE \'utc\'',
    'AND start_at IS NULL',
    'AND done_at IS NULL',
    'AND fail_at IS NULL',
    'ORDER BY start_after',
    'LIMIT $1',
    'FOR UPDATE SKIP LOCKED',
)

TASK_UPDATE_WORK = _(
    'UPDATE obx.tasks SET',
    'updated_at = now(),',
    'start_at = now()',
    'WHERE id = any($1)',
)

TASK_UPDATE_DONE = _(
    'UPDATE obx.tasks SET',
    'updated_at = now(),',
    'start_after =',
    '  CASE',
    '  WHEN delta_done IS NULL',
    '  THEN start_after',
    '  ELSE',
    '    CASE',
    '    WHEN start_after + delta_done > now()',
    '    THEN start_after + delta_done',
    '    ELSE now() + delta_done',
    '    END',
    '  END,',
    'start_at =',
    '  CASE',
    '  WHEN delta_done IS NULL',
    '  THEN start_at',
    '  ELSE NULL',
    '  END,',
    'done_at =',
    '  CASE',
    '  WHEN delta_done IS NULL',
    '  THEN now()',
    '  ELSE NULL',
    '  END',
    'WHERE id = $1',
)

TASK_UPDATE_FAIL = _(
    'UPDATE obx.tasks SET',
    'updated_at = now(),',
    'start_after =',
    '  CASE',
    '  WHEN delta_fail IS NULL',
    '  THEN start_after',
    '  ELSE',
    '    CASE',
    '    WHEN start_after + delta_fail > now()',
    '    THEN start_after + delta_fail',
    '    ELSE now() + delta_fail',
    '    END',
    '  END,',
    'start_at =',
    '  CASE',
    '  WHEN delta_fail IS NULL',
    '  THEN start_at',
    '  ELSE NULL',
    '  END,',
    'fail_at =',
    '  CASE',
    '  WHEN delta_fail IS NULL',
    '  THEN now()',
    '  ELSE NULL',
    '  END,',
    'error = $2',
    'WHERE id = $1',
)

TASK_UPDATE_TIMEOUT = _(
    'UPDATE obx.tasks SET',
    'updated_at = now(),',
    'start_after =',
    '  CASE',
    '  WHEN delta_fail IS NULL',
    '  THEN start_after',
    '  ELSE',
    '    CASE',
    '    WHEN start_after + delta_fail > now()',
    '    THEN start_after + delta_fail',
    '    ELSE now() + delta_fail',
    '    END',
    '  END,',
    'start_at =',
    '  CASE',
    '  WHEN delta_fail IS NULL',
    '  THEN start_at',
    '  ELSE NULL',
    '  END,',
    'fail_at =',
    '  CASE',
    '  WHEN delta_fail IS NULL',
    '  THEN now()',
    '  ELSE NULL',
    '  END,',
    'error = \'timeout\'',
    'WHERE start_at + cast(delta_timeout AS time) < now()',
    'AND done_at IS NULL',
    'AND fail_at IS NULL',
)
