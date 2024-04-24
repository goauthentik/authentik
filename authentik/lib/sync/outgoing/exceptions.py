from authentik.lib.sentry import SentryIgnoredException


class BaseSyncException(SentryIgnoredException):
    """Base class for all sync exceptions"""


class TransientSyncException(BaseSyncException):
    """Transient sync exception which may be caused by network blips, etc"""


class StopSync(BaseSyncException):
    """Exception raised when a configuration error should stop the sync process"""

    def __init__(self, exc: Exception, obj: object, mapping: object | None = None) -> None:
        self.exc = exc
        self.obj = obj
        self.mapping = mapping

    def detail(self) -> str:
        """Get human readable details of this error"""
        msg = f"Error {str(self.exc)}, caused by {self.obj}"

        if self.mapping:
            msg += f" (mapping {self.mapping})"
        return msg
