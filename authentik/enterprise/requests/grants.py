"""Persistence of grant requests, shared by the browser flow's final stage and the headless
agent endpoint."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest
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
from authentik.lib.utils.time import timedelta_to_string
from authentik.policies.models import PolicyBindingModel


@dataclass(frozen=True)
class GrantExpiry:
    """The two durations a request carries: how long it stays pending before lapsing, and how
    long the grant lasts once approved."""

    pending: timedelta
    granted: timedelta


def fulfill_url(request: HttpRequest, req: GrantRequest) -> str:
    """The page an approver opens to act on `req`. Also what an agent hands back to the human
    it acts for, since it has no browser of its own to run an approval in."""
    return (
        request.build_absolute_uri(reverse("authentik_core:if-user"))
        + f"#/requests/access-request/{req.uuid}/fulfill"
    )


def assign_request_permissions(
    rules: QuerySet[RequestRule], req: GrantRequest, agent_owner: User | None = None
):
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
    if agent_owner:
        # An agent's owner must approve its request, so they need the same object-level access
        # a reviewer gets -- whether or not any rule makes them an eligible reviewer, and even
        # when the request carries no rule at all.
        reviewers.add(agent_owner)
    for reviewer in reviewers:
        reviewer.assign_perms_to_managed_role(
            [
                "authentik_requests.view_grantrequest",
                "authentik_requests.fulfill_grantrequest",
                "authentik_requests.revoke_grantrequest",
            ],
            req,
        )


def notify_reviewers(rules: QuerySet[RequestRule], event: Event):
    """Notify reviewers of each rule attached to any of the requested targets,
    per that rule's own notification_transports/notification_mode. An agent request resolves no
    rules, so nothing is dispatched for one -- its owner reaches it through the `fulfill_url`
    handed back to the agent, and through `pending_review`."""
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


def create_grant_request(
    request: HttpRequest,
    *,
    created_by: User,
    pbms: list[PolicyBindingModel],
    requester_data: dict[str, Any],
    expiry: GrantExpiry,
    agent_owner: User | None = None,
) -> GrantRequest:
    """Persist a grant request against `pbms`, assign the object permissions the requester,
    reviewers and (for an agent) its owner need to act on it, and notify them."""
    with transaction.atomic(), audit_ignore():
        req = GrantRequest.objects.create(
            created_by=created_by,
            requester_data=requester_data,
            requested_expiry=timedelta_to_string(expiry.granted),
            expiring=True,
            expires=now() + expiry.pending,
            status=RequestStatus.CREATED,
            agent_owner=agent_owner,
        )
        for pbm in pbms:
            GrantRequestTarget.objects.create(
                request=req,
                target=pbm,
                binding=None,
            )
        # An agent request is decided by its owner alone, so RequestRules attached to the target
        # play no part: their reviewers must not be handed fulfill/revoke on it, and telling
        # them about a request they have no say in would only leak it.
        rules = (
            RequestRule.objects.none()
            if agent_owner
            else RequestRule.objects.filter(targets__in=pbms)
            .distinct()
            .prefetch_related("notification_transports")
        )
        assign_request_permissions(rules, req, agent_owner)
        event = Event.new(
            EventAction.ACCESS_REQUEST_CREATED,
            model=req,
            targets=pbms,
            hyperlink=fulfill_url(request, req),
            hyperlink_label="Fulfill",
        ).from_http(request, created_by)
        notify_reviewers(rules, event)
    return req
