"""passbook consent stage"""
from typing import Any, Dict, List

from django.views.generic import FormView

from passbook.flows.stage import StageView
from passbook.stages.consent.forms import ConsentForm

PLAN_CONTEXT_CONSENT_TEMPLATE = "consent_template"


class ConsentStageView(FormView, StageView):
    """Simple consent checker."""

    form_class = ConsentForm

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs["current_stage"] = self.executor.current_stage
        kwargs["context"] = self.executor.plan.context
        return kwargs

    def get_template_names(self) -> List[str]:
        if PLAN_CONTEXT_CONSENT_TEMPLATE in self.executor.plan.context:
            template_name = self.executor.plan.context[PLAN_CONTEXT_CONSENT_TEMPLATE]
            return [template_name]
        return super().get_template_names()

    def form_valid(self, form):
        return self.executor.stage_ok()
