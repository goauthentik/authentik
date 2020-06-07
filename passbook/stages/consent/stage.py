"""passbook consent stage"""
from typing import Any, Dict

from django.views.generic import FormView

from passbook.flows.stage import StageView
from passbook.lib.utils.template import render_to_string
from passbook.stages.consent.forms import ConsentForm


class ConsentStage(FormView, StageView):
    """Simple consent checker."""

    body_template_name: str

    form_class = ConsentForm

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        if self.body_template_name:
            kwargs["body"] = render_to_string(self.body_template_name, kwargs)
        return kwargs

    def form_valid(self, form):
        return self.executor.stage_ok()
