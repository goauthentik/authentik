"""SCIM Client exceptions"""
from authentik.lib.sentry import SentryIgnoredException


class SCIMRequestError(SentryIgnoredException):
    """Error raised when an SCIM request fails"""
