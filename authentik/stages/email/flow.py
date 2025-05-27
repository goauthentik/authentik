from base64 import b64encode
from pickle import dumps  # nosec

from django.db import Error
from django.utils.translation import gettext as _

from authentik.flows.models import FlowToken, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_IS_RESTORED, FlowPlan
from authentik.stages.consent.stage import PLAN_CONTEXT_CONSENT_HEADER, ConsentStageView


def pickle_flow_token_for_email(plan: FlowPlan):
    """Insert a consent stage into the flow plan and pickle it for a FlowToken,
    to be sent via Email. This is to prevent automated email scanners, which sometimes
    open links in emails in a full browser from breaking the link."""
    plan.insert_stage(in_memory_stage(EmailTokenRevocationConsentStageView), index=0)
    plan.context[PLAN_CONTEXT_CONSENT_HEADER] = _("Continue to confirm this email address.")
    data = dumps(plan)
    return b64encode(data).decode()


class EmailTokenRevocationConsentStageView(ConsentStageView):

    def get_challenge(self):
        token: FlowToken = self.executor.plan.context[PLAN_CONTEXT_IS_RESTORED]
        try:
            token.refresh_from_db()
        except Error:
            return self.executor.stage_invalid(
                _("Link was already used, please request a new link.")
            )
        return super().get_challenge()

    def challenge_valid(self, response):
        token: FlowToken = self.executor.plan.context[PLAN_CONTEXT_IS_RESTORED]
        token.delete()
        return super().challenge_valid(response)
