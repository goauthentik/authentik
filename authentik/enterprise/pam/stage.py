from datetime import timedelta

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.timezone import now

from authentik.enterprise.pam.models import GrantRequest, GrantRequestTarget, RequestStatus
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.flows.stage import StageView
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_GRANT_REQUESTED_PBMS = "goauthentik.io/pam/requested-pbms"
PLAN_CONTEXT_GRANT_REQUESTED_PERSONA = "goauthentik.io/pam/requested-persona"


class GrantRequestFinalStageView(StageView):

    def get(self, request: HttpRequest) -> HttpResponse:
        user = self.get_pending_user()
        pbms = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_REQUESTED_PBMS)
        persona = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_REQUESTED_PERSONA)
        expires = now() + timedelta(hours=1)
        with transaction.atomic(), audit_ignore():
            req = GrantRequest.objects.create(
                created_by=user,
                persona=persona,
                requester_data=self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}),
                expiring=True,
                expires=expires,
                status=RequestStatus.CREATED,
            )
            for pbm in pbms:
                GrantRequestTarget.objects.create(
                    request=req,
                    target=pbm,
                    binding=None,
                )
            Event.new(
                EventAction.ACCESS_REQUEST_CREATED,
                model=req,
                targets=pbms,
                hyperlink=request.build_absolute_uri(reverse("authentik_core:if-admin"))
                + f"#/pam/requests/{req.uuid}/fulfill",
                hyperlink_label="Fulfill",
            ).from_http(request, user)
        return self.executor.stage_ok()

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
