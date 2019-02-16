"""passbook multi-factor authentication engine"""
from logging import getLogger

from passbook.core.auth.factor import AuthenticationFactor
from passbook.core.auth.factor_manager import MANAGER

LOGGER = getLogger(__name__)


@MANAGER.factor()
class DummyFactor(AuthenticationFactor):
    """Dummy factor for testing with multiple factors"""

    def post(self, request):
        """Just redirect to next factor"""
        return self.authenticator.user_ok()
