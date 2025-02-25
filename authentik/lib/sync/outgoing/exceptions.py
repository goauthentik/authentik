from authentik.lib.sentry import SentryIgnoredException


class BaseSyncException(SentryIgnoredException):
    """Base class for all sync exceptions"""


class TransientSyncException(BaseSyncException):
    """Transient sync exception which may be caused by network blips, etc"""


class NotFoundSyncException(BaseSyncException):
    """Exception when an object was not found in the remote system"""


class ObjectExistsSyncException(BaseSyncException):
    """Exception when an object already exists in the remote system"""


class BadRequestSyncException(BaseSyncException):
    """Exception when invalid data was sent to the remote system"""


class DryRunRejected(BaseSyncException):
    """When dry_run is enabled and a provider dropped a mutating request"""

    def __init__(self, url: str, method: str, body: dict):
        super().__init__()
        self.url = url
        self.method = method
        self.body = body

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
