"""authentik core exceptions"""

from authentik.lib.sentry import SentryIgnoredException


class PropertyMappingExpressionException(SentryIgnoredException):
    """Error when a PropertyMapping Exception expression could not be parsed or evaluated."""

    def __init__(self, exc: Exception, mapping) -> None:
        super().__init__()
        self.exc = exc
        self.mapping = mapping


class SkipObjectException(PropertyMappingExpressionException):
    """Exception which can be raised in a property mapping to skip syncing an object.
    Only applies to Property mappings which sync objects, and not on mappings which transitively
    apply to a single user"""

    def __init__(self) -> None:
        # For this class only, both of these are set by the function evaluating the property mapping
        super().__init__(exc=None, mapping=None)
