"""policy exceptions"""
from passbook.lib.sentry import SentryIgnoredException


class PolicyException(SentryIgnoredException):
    """Exception that should be raised during Policy Evaluation, and can be recovered from."""
