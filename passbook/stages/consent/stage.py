"""passbook consent stage"""
from typing import Any, Dict, List

from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now
from django.views.generic import FormView

from passbook.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import StageView
from passbook.lib.utils.time import timedelta_from_string
from passbook.stages.consent.forms import ConsentForm
from passbook.stages.consent.models import ConsentMode, ConsentStage, UserConsent

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
        # PLAN_CONTEXT_CONSENT_TEMPLATE has to be set by a template that calls this stage
        # TODO: Add a default template in case a user directly implements this stage
        if PLAN_CONTEXT_CONSENT_TEMPLATE in self.executor.plan.context:
            template_name = self.executor.plan.context[PLAN_CONTEXT_CONSENT_TEMPLATE]
            return [template_name]
        return super().get_template_names()

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        current_stage: ConsentStage = self.executor.current_stage
        # For always require, we always show the form
        if current_stage.mode == ConsentMode.ALWAYS_REQUIRE:
            return super().get(request, *args, **kwargs)
        # at this point we need to check consent from database
        if PLAN_CONTEXT_APPLICATION not in self.executor.plan.context:
            # No application in this plan, hence we can't check DB and require user consent
            return super().get(request, *args, **kwargs)

        application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]

        user = self.request.user
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]

        if UserConsent.filter_not_expired(
            user=user, application=application
        ).exists():
            return self.executor.stage_ok()

        # No consent found, show form
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: ConsentForm) -> HttpResponse:
        current_stage: ConsentStage = self.executor.current_stage
        if PLAN_CONTEXT_APPLICATION not in self.executor.plan.context:
            return self.executor.stage_ok()
        application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        # Since we only get here when no consent exists, we can create it without update
        if current_stage.mode == ConsentMode.PERMANENT:
            UserConsent.objects.create(
                user=self.request.user, application=application, expiring=False
            )
        if current_stage.mode == ConsentMode.EXPIRING:
            UserConsent.objects.create(
                user=self.request.user,
                application=application,
                expires=now() + timedelta_from_string(current_stage.consent_expire_in),
            )
        return self.executor.stage_ok()
