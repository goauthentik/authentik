from datetime import timedelta

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.timezone import now

from authentik.enterprise.pam.models import (
    GrantRequest,
    GrantRequestTarget,
    PolicyBindingModelRequestRule,
    RequestStatus,
)
from authentik.enterprise.pam.tasks import pam_request_notification
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.flows.stage import StageView
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
            event = Event.new(
                EventAction.ACCESS_REQUEST_CREATED,
                model=req,
                targets=pbms,
                hyperlink=request.build_absolute_uri(reverse("authentik_core:if-admin"))
                + f"#/pam/requests/{req.uuid}/fulfill",
                hyperlink_label="Fulfill",
            ).from_http(request, user)
            self._notify_reviewers(pbms, event)
        return self.executor.stage_ok()

    def _notify_reviewers(self, pbms: list, event: Event):
        """Notify reviewers of each rule attached to any of the requested targets,
        per that rule's own notification_transports/notification_mode."""
        rules = (
            PolicyBindingModelRequestRule.objects.filter(pbms__in=pbms)
            .distinct()
            .prefetch_related("notification_transports", "reviewers", "reviewer_groups")
        )
        for rule in rules:
            transports = list(rule.notification_transports.all())
            if not transports:
                continue
            for recipient in rule.notification_recipients():
                for transport in transports:
                    pam_request_notification.send_with_options(
                        args=(transport.pk, event.pk, recipient.pk),
                        rel_obj=transport,
                    )

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
