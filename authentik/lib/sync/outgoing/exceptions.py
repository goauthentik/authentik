from json import JSONDecodeError

from authentik.lib.sentry import SentryIgnoredException


class BaseSyncException(SentryIgnoredException):
    """Base class for all sync exceptions"""


class TransientSyncException(BaseSyncException):
    """Transient sync exception which may be caused by network blips, etc"""

    def __init__(self, response=None):
        super().__init__()
        self.response = response

    def __str__(self):
        if self.response is not None:
            if hasattr(self.response, "json"):
                try:
                    return f"Network error: {self.response.json()}"
                except JSONDecodeError:
                    pass
            if hasattr(self.response, "text"):
                return f"Network error: {self.response.text}"
            return f"Network error: {self.response}"
        return "Network error communicating with remote system"

    def __repr__(self):
        return self.__str__()


class NotFoundSyncException(BaseSyncException):
    """Exception when an object was not found in the remote system"""

    def __init__(self, response=None):
        super().__init__()
        self.response = response

    def __str__(self):
        if self.response is not None:
            if hasattr(self.response, "json"):
                try:
                    return f"Object not found: {self.response.json()}"
                except JSONDecodeError:
                    pass
            if hasattr(self.response, "text"):
                return f"Object not found: {self.response.text}"
            return f"Object not found: {self.response}"
        return "Object not found in remote system"

    def __repr__(self):
        return self.__str__()


class ObjectExistsSyncException(BaseSyncException):
    """Exception when an object already exists in the remote system"""

    def __init__(self, response=None):
        super().__init__()
        self.response = response

    def __str__(self):
        if self.response is not None:
            if hasattr(self.response, "json"):
                try:
                    return f"Object exists: {self.response.json()}"
                except JSONDecodeError:
                    pass
            if hasattr(self.response, "text"):
                return f"Object exists: {self.response.text}"
            return f"Object exists: {self.response}"
        return "Object exists in remote system"

    def __repr__(self):
        return self.__str__()


class BadRequestSyncException(BaseSyncException):
    """Exception when invalid data was sent to the remote system"""

    def __init__(self, response=None):
        super().__init__()
        self.response = response

    def __str__(self):
        if self.response is not None:
            if hasattr(self.response, "json"):
                try:
                    return f"Bad request: {self.response.json()}"
                except JSONDecodeError:
                    pass
            if hasattr(self.response, "text"):
                return f"Bad request: {self.response.text}"
            return f"Bad request: {self.response}"
        return "Bad request to remote system"

    def __repr__(self):
        return self.__str__()


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
