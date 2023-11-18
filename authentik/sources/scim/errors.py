"""SCIM Errors"""

from authentik.lib.sentry import SentryIgnoredException


class PatchError(SentryIgnoredException):
    """Error raised within an atomic block when an error happened
    so nothing is saved"""
