"""passbook multi-stage authentication engine"""
from django.http import HttpRequest

from passbook.flows.stage import AuthenticationStage


class DummyStage(AuthenticationStage):
    """Dummy stage for testing with multiple stages"""

    def post(self, request: HttpRequest):
        """Just redirect to next stage"""
        return self.executor.stage_ok()
