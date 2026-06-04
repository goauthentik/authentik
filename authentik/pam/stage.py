from django.db import transaction
from django.http import HttpRequest

from authentik.flows.stage import StageView
from authentik.pam.models import GrantRequest, GrantRequestTarget
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_GRANT_REQUESTED_PBMS = "goauthentik.io/pam/requested-pbms"


class GrantRequestFinalStageView(StageView):
    def get(self, request: HttpRequest):
        user = self.get_pending_user()
        pbms = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_REQUESTED_PBMS)
        with transaction.atomic():
            req = GrantRequest(
                created_by=user, data=self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {})
            )
            for pbm in pbms:
                GrantRequestTarget.objects.create(
                    request=req,
                    target=pbm,
                )
