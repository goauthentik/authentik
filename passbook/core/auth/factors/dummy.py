"""passbook multi-factor authentication engine"""
from structlog import get_logger

from passbook.core.auth.factor import AuthenticationFactor

LOGGER = get_logger()


class DummyFactor(AuthenticationFactor):
    """Dummy factor for testing with multiple factors"""

    def post(self, request):
        """Just redirect to next factor"""
        return self.authenticator.user_ok()
