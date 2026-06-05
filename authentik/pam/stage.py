from datetime import timedelta

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now

from authentik.flows.stage import StageView
from authentik.pam.models import GrantRequest, GrantRequestTarget, RequestState
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_GRANT_REQUESTED_PBMS = "goauthentik.io/pam/requested-pbms"


class GrantRequestFinalStageView(StageView):

    def get(self, request: HttpRequest) -> HttpResponse:
        user = self.get_pending_user()
        pbms = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_REQUESTED_PBMS)
        expires = now() + timedelta(hours=1)
        with transaction.atomic():
            req = GrantRequest(
                created_by=user,
                data=self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}),
                expiring=True,
                expires=expires,
                status=RequestState.CREATED,
            )
            for pbm in pbms:
                GrantRequestTarget.objects.create(
                    request=req,
                    target=pbm,
                    binding=None,
                )
        return self.executor.stage_ok()

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
