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
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

PLAN_CONTEXT_GRANT_REQUESTED_PBMS = "goauthentik.io/requests/requested-pbms"
PLAN_CONTEXT_GRANT_PENDING_EXPIRY = "goauthentik.io/requests/pending-expiry"
PLAN_CONTEXT_GRANT_MAX_EXPIRY = "goauthentik.io/requests/max-expiry"
PLAN_CONTEXT_GRANT_REQUESTED_EXPIRY = "goauthentik.io/requests/requested-expiry"


class GrantRequestFinalStageView(StageView):

    def get(self, request: HttpRequest) -> HttpResponse:
        user = self.get_pending_user()
        pbms = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_REQUESTED_PBMS)
        pending_expiry = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_PENDING_EXPIRY)
        max_expiry = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_MAX_EXPIRY)
        requested_expiry = self.executor.plan.context.get(PLAN_CONTEXT_GRANT_REQUESTED_EXPIRY)
        # Enforce the configured maximum here, at persistence time, rather than
        # earlier in create() -- a stage in the flow may have changed the requested
        # duration since, so the ceiling can only be safely applied at the end.
        granted_expiry_candidates = [max_expiry]
        if requested_expiry:
            granted_expiry_candidates.append(requested_expiry)
        granted_expiry = min(granted_expiry_candidates, key=timedelta_from_string)
        with transaction.atomic(), audit_ignore():
            req = GrantRequest.objects.create(
                created_by=user,
                requester_data=self.executor.plan.context.get(PLAN_CONTEXT_PROMPT, {}),
                requested_expiry=granted_expiry,
                expiring=True,
                expires=now() + timedelta_from_string(pending_expiry),
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
                    "authentik_requests.fulfill_grantrequest",
                    "authentik_requests.revoke_grantrequest",
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
