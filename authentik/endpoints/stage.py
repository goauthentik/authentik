from authentik.endpoints.models import EndpointStage
from authentik.flows.stage import StageView

PLAN_CONTEXT_ENDPOINT_CONNECTOR = "endpoint_connector"


class EndpointStageView(StageView):

    def dispatch(self, request, *args, **kwargs):
        stage: EndpointStage = self.executor.current_stage
        inner_stage: type[StageView] | None = stage.connector.stage
        if not inner_stage:
            return self.executor.stage_ok()
        view = inner_stage(self.executor, request=self.request)
        return view.dispatch(request, *args, **kwargs)
