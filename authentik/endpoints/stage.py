from authentik.endpoints.models import EndpointStage
from authentik.flows.stage import StageView

PLAN_CONTEXT_ENDPOINT_CONNECTOR = "endpoint_connector"


class EndpointStageView(StageView):

    def _get_inner(self):
        stage: EndpointStage = self.executor.current_stage
        inner_stage: type[StageView] | None = stage.connector.stage
        if not inner_stage:
            return self.executor.stage_ok()
        return inner_stage(self.executor, request=self.request)

    def dispatch(self, request, *args, **kwargs):
        return self._get_inner().dispatch(request, *args, **kwargs)

    def cleanup(self):
        return self._get_inner().cleanup()
