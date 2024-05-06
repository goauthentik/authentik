"""authentik core exceptions"""

from authentik.lib.sentry import SentryIgnoredException


class PropertyMappingExpressionException(SentryIgnoredException):
    """Error when a PropertyMapping Exception expression could not be parsed or evaluated."""


class SkipObjectException(PropertyMappingExpressionException):
    """Exception which can be raised in a property mapping to skip syncing an object.
    Only applies to Property mappings which sync objects, and not on mappings which transitively
    apply to a single user"""
