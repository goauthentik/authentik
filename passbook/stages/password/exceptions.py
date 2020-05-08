"""passbook password policy exceptions"""
from passbook.lib.sentry import SentryIgnoredException


class PasswordPolicyInvalid(SentryIgnoredException):
    """Exception raised when a Password Policy fails"""

    messages = []

    def __init__(self, *messages):
        super().__init__()
        self.messages = messages
