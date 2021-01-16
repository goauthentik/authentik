"""policy exceptions"""
from typing import Optional

from authentik.lib.sentry import SentryIgnoredException


class PolicyException(SentryIgnoredException):
    """Exception that should be raised during Policy Evaluation, and can be recovered from."""

    src_exc: Optional[Exception] = None

    def __init__(self, src_exc: Optional[Exception] = None) -> None:
        super().__init__()
        self.src_exc = src_exc
