"""Event Matcher models"""
from typing import Type

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer
from authentik.events.models import Event, EventAction

from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult


class EventMatcherPolicy(Policy):
    """Passes when Event matches selected criteria."""

    action = models.TextField(choices=EventAction.choices, blank=True)
    client_ip = models.TextField(blank=True)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.policies.event_matcher.api import (
            EventMatcherPolicySerializer,
        )

        return EventMatcherPolicySerializer

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.policies.event_matcher.forms import EventMatcherPolicyForm

        return EventMatcherPolicyForm

    def passes(self, request: PolicyRequest) -> PolicyResult:
        if 'event' not in request.context:
            return PolicyResult(False)
        event: Event = request.context['event']
        if self.action != "":
            if event.action != self.action:
                return PolicyResult(False, "Action did not match.")
        if self.client_ip != "":
            if event.client_ip != self.client_ip:
                return PolicyResult(False, "Client IP did not match.")
        return PolicyResult(True)

    class Meta:

        verbose_name = _("Group Membership Policy")
        verbose_name_plural = _("Group Membership Policies")
