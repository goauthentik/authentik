from datetime import timedelta

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.timezone import now

from authentik.core.models import User
from authentik.enterprise.requests.models import (
    GrantRequest,
    GrantRequestTarget,
    RequestRule,
    RequestStatus,
)
from authentik.enterprise.requests.tasks import requests_send_request_notification
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.flows.stage import StageView
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_GRANT_REQUESTED_PBMS = "goauthentik.io/requests/requested-pbms"


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
            rules = (
                RequestRule.objects.filter(targets__in=pbms)
                .distinct()
                .prefetch_related("notification_transports")
            )
            self._assign_permissions(rules, req)
            event = Event.new(
                EventAction.ACCESS_REQUEST_CREATED,
                model=req,
                targets=pbms,
                hyperlink=request.build_absolute_uri(reverse("authentik_core:if-user"))
                + f"#/requests/access-request/{req.uuid}/fulfill",
                hyperlink_label="Fulfill",
            ).from_http(request, user)
            self._notify_reviewers(rules, event)
        return self.executor.stage_ok()

    @staticmethod
    def _assign_permissions(rules, req: GrantRequest):
        """Grant the requester and every reviewer eligible for any of `rules`
        object-level permission on `req`, so they can see and act on it without
        needing a blanket, org-wide grant of those permissions."""
        req.created_by.assign_perms_to_managed_role(
            ["authentik_requests.view_grantrequest", "authentik_requests.delete_grantrequest"],
            req,
        )
        reviewers: set[User] = set()
        for rule in rules:
            reviewers.update(rule.reviewers_among(User.objects.all()))
        for reviewer in reviewers:
            reviewer.assign_perms_to_managed_role(
                [
                    "authentik_requests.view_grantrequest",
                    "authentik_requests.change_grantrequest",
                    "authentik_requests.add_grantrequest",
                ],
                req,
            )

    @staticmethod
    def _notify_reviewers(rules, event: Event):
        """Notify reviewers of each rule attached to any of the requested targets,
        per that rule's own notification_transports/notification_mode."""
        for rule in rules:
            transports = list(rule.notification_transports.all())
            if not transports:
                continue
            for recipient in rule.notification_recipients():
                for transport in transports:
                    requests_send_request_notification.send_with_options(
                        args=(transport.pk, event.pk, recipient.pk),
                        rel_obj=transport,
                    )

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
