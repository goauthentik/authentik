from authentik.endpoints.models import EndpointStage
from authentik.flows.stage import StageView

PLAN_CONTEXT_ENDPOINT_CONNECTOR = "endpoint_connector"


class EndpointStageView(StageView):

    def _get_inner(self) -> StageView | None:
        stage: EndpointStage = self.executor.current_stage
        inner_stage: type[StageView] | None = stage.connector.stage
        if not inner_stage:
            return None
        return inner_stage(self.executor, request=self.request)

    def dispatch(self, request, *args, **kwargs):
        inner = self._get_inner()
        if inner is None:
            return self.executor.stage_ok()
        return inner.dispatch(request, *args, **kwargs)

    def cleanup(self):
        inner = self._get_inner()
        if inner is not None:
            return inner.cleanup()
