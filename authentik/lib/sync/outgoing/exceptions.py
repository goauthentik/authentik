from authentik.lib.sentry import SentryIgnoredException


class StopSync(SentryIgnoredException):
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
