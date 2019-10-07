"""passbook multi-factor authentication engine"""
from django.http import HttpRequest

from passbook.factors.base import AuthenticationFactor


class DummyFactor(AuthenticationFactor):
    """Dummy factor for testing with multiple factors"""

    def post(self, request: HttpRequest):
        """Just redirect to next factor"""
        return self.authenticator.user_ok()
