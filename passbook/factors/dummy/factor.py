"""passbook multi-factor authentication engine"""
from django.http import HttpRequest

from passbook.flows.factor_base import AuthenticationFactor


class DummyFactor(AuthenticationFactor):
    """Dummy factor for testing with multiple factors"""

    def post(self, request: HttpRequest):
        """Just redirect to next factor"""
        return self.executor.factor_ok()
