"""authentik core exceptions"""

from django.core.exceptions import SuspiciousOperation


class SessionSuperseded(SuspiciousOperation):
    """Raised when a session was replaced by a newer login in the same browser.

    A SuspiciousOperation so the session store discards the session, but an expected,
    routine outcome of user switching rather than a genuinely suspicious request.
    """
