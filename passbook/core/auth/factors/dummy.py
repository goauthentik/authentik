"""passbook multi-factor authentication engine"""
from logging import getLogger

from passbook.core.auth.factor import AuthenticationFactor

LOGGER = getLogger(__name__)


class DummyFactor(AuthenticationFactor):
    """Dummy factor for testing with multiple factors"""

    def post(self, request):
        """Just redirect to next factor"""
        return self.authenticator.user_ok()
