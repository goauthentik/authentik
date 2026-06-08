from datetime import timedelta

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.timezone import now

from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.flows.stage import StageView
from authentik.pam.models import GrantRequest, GrantRequestTarget, RequestStatus
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_GRANT_REQUESTED_PBMS = "goauthentik.io/pam/requested-pbms"


class GrantRequestFinalStageView(StageView):

    def get(self, request: HttpRequest) -> HttpResponse:
        user = self.get_pending_user()
        pbms = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_REQUESTED_PBMS)
        expires = now() + timedelta(hours=1)
        with transaction.atomic(), audit_ignore():
            req = GrantRequest.objects.create(
                created_by=user,
                data=self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}),
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
                EventAction.MODEL_CREATED,
                model=req,
                hyperlink=request.build_absolute_uri(reverse("authentik_core:if-admin"))
                + f"#/pam/requests/{req.uuid}/respond",
                hyperlink_label="Respond",
            ).from_http(request, user)
        return self.executor.stage_ok()

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
