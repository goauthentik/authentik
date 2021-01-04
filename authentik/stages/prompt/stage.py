"""Prompt Stage Logic"""
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from structlog.stdlib import get_logger

from authentik.flows.stage import StageView
from authentik.stages.prompt.forms import PromptForm

LOGGER = get_logger()
PLAN_CONTEXT_PROMPT = "prompt_data"


class PromptStageView(FormView, StageView):
    """Prompt Stage, save form data in plan context."""

    template_name = "login/form.html"
    form_class = PromptForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _(self.executor.current_stage.name)
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["stage"] = self.executor.current_stage
        kwargs["plan"] = self.executor.plan
        return kwargs

    def form_valid(self, form: PromptForm) -> HttpResponse:
        """Form data is valid"""
        if PLAN_CONTEXT_PROMPT not in self.executor.plan.context:
            self.executor.plan.context[PLAN_CONTEXT_PROMPT] = {}
        self.executor.plan.context[PLAN_CONTEXT_PROMPT].update(form.cleaned_data)
        return self.executor.stage_ok()
