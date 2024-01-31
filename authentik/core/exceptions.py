"""authentik core exceptions"""

from authentik.lib.sentry import SentryIgnoredException


class PropertyMappingExpressionException(SentryIgnoredException):
    """Error when a PropertyMapping Exception expression could not be parsed or evaluated."""
