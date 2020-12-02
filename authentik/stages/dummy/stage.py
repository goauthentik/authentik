"""authentik multi-stage authentication engine"""
from typing import Any, Dict

from django.http import HttpRequest

from authentik.flows.stage import StageView


class DummyStageView(StageView):
    """Dummy stage for testing with multiple stages"""

    def post(self, request: HttpRequest):
        """Just redirect to next stage"""
        return self.executor.stage_ok()

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs["title"] = self.executor.current_stage.name
        return kwargs
