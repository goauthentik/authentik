from json import JSONDecodeError

from authentik.lib.sentry import SentryIgnoredException


class BaseSyncException(SentryIgnoredException):
    """Base class for all sync exceptions"""

    error_prefix = "Sync error"
    error_default = "Error communicating with remote system"

    def __init__(self, response=None):
        super().__init__()
        self.response = response

    def __str__(self):
        if self.response is not None:
            if hasattr(self.response, "json"):
                try:
                    return f"{self.error_prefix}: {self.response.json()}"
                except JSONDecodeError:
                    pass
            if hasattr(self.response, "text"):
                return f"{self.error_prefix}: {self.response.text}"
            return f"{self.error_prefix}: {self.response}"
        return self.error_default

    def __repr__(self):
        return self.__str__()


class TransientSyncException(BaseSyncException):
    """Transient sync exception which may be caused by network blips, etc"""

    error_prefix = "Network error"
    error_default = "Network error communicating with remote system"


class NotFoundSyncException(BaseSyncException):
    """Exception when an object was not found in the remote system"""

    error_prefix = "Object not found"
    error_default = "Object not found in remote system"


class ObjectExistsSyncException(BaseSyncException):
    """Exception when an object already exists in the remote system"""

    error_prefix = "Object exists"
    error_default = "Object exists in remote system"


class BadRequestSyncException(BaseSyncException):
    """Exception when invalid data was sent to the remote system"""

    error_prefix = "Bad request"
    error_default = "Bad request to remote system"


class DryRunRejected(BaseSyncException):
    """When dry_run is enabled and a provider dropped a mutating request"""

    def __init__(self, url: str, method: str, body: dict):
        super().__init__()
        self.url = url
        self.method = method
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Dry-run rejected request: {self.method} {self.url}"


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
