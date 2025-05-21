class ObxError(Exception):
    pass


class ConnectionNotSetObxError(ObxError):
    pass


class ConnectionTypeNotSetObxError(ObxError):
    pass


class ConnectionTypeUnknownObxError(ObxError):
    pass


class PoolNotSetObxError(ObxError):
    pass


class TaskHandlerNotSetObxError(ObxError):
    pass


class TaskStateUnknownObxError(ObxError):
    pass
