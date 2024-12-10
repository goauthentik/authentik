from authentik.lib.sentry import SentryIgnoredException


class BaseSyncException(SentryIgnoredException):
    """Base class for all sync exceptions"""


class TransientSyncException(BaseSyncException):
    """Transient sync exception which may be caused by network blips, etc"""


class BadRequestSyncException(BaseSyncException):
    """Exception when invalid data was sent to the remote system"""


class NotFoundSyncException(BadRequestSyncException):
    """Exception when an object was not found in the remote system"""


class ObjectExistsSyncException(BadRequestSyncException):
    """Exception when an object already exists in the remote system"""


class StopSync(BaseSyncException):
    """Exception raised when a configuration error should stop the sync process"""

    def __init__(
        self, exc: Exception, obj: object | None = None, mapping: object | None = None
    ) -> None:
        self.exc = exc
        self.obj = obj
        self.mapping = mapping

    def detail(self) -> str:
        """Get human readable details of this error"""
        msg = f"Error {str(self.exc)}"
        if self.obj:
            msg += f", caused by {self.obj}"
        if self.mapping:
            msg += f" (mapping {self.mapping})"
        return msg
