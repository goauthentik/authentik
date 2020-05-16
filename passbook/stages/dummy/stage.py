"""passbook multi-stage authentication engine"""
from django.http import HttpRequest

from passbook.flows.stage import StageView


class DummyStage(StageView):
    """Dummy stage for testing with multiple stages"""

    def post(self, request: HttpRequest):
        """Just redirect to next stage"""
        return self.executor.stage_ok()
