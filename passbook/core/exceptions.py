"""passbook core exceptions"""
from passbook.lib.sentry import SentryIgnoredException


class PropertyMappingExpressionException(SentryIgnoredException):
    """Error when a PropertyMapping Exception expression could not be parsed or evaluated."""
