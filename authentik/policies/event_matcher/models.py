"""Event Matcher models"""
from typing import Type

from django.apps import apps
from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer

from authentik.events.models import Event, EventAction
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult


def app_choices() -> list[tuple[str, str]]:
    """Get a list of all installed applications that create events.
    Returns a list of tuples containing (dotted.app.path, name)"""
    choices = []
    for app in apps.get_app_configs():
        if app.label.startswith("authentik"):
            choices.append((app.name, app.verbose_name))
    return choices


class EventMatcherPolicy(Policy):
    """Passes when Event matches selected criteria."""

    action = models.TextField(
        choices=EventAction.choices,
        blank=True,
        help_text=_(
            (
                "Match created events with this action type. "
                "When left empty, all action types will be matched."
            )
        ),
    )
    app = models.TextField(
        choices=app_choices(),
        blank=True,
        default="",
        help_text=_(
            (
                "Match events created by selected application. "
                "When left empty, all applications are matched."
            )
        ),
    )
    client_ip = models.TextField(
        blank=True,
        help_text=_(
            (
                "Matches Event's Client IP (strict matching, "
                "for network matching use an Expression Policy)"
            )
        ),
    )

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.policies.event_matcher.api import EventMatcherPolicySerializer

        return EventMatcherPolicySerializer

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.policies.event_matcher.forms import EventMatcherPolicyForm

        return EventMatcherPolicyForm

    def passes(self, request: PolicyRequest) -> PolicyResult:
        if "event" not in request.context:
            return PolicyResult(False)
        event: Event = request.context["event"]
        if event.action == self.action:
            return PolicyResult(True, "Action matched.")
        if event.client_ip == self.client_ip:
            return PolicyResult(True, "Client IP matched.")
        if event.app == self.app:
            return PolicyResult(True, "App matched.")
        return PolicyResult(False)

    class Meta:

        verbose_name = _("Event Matcher Policy")
        verbose_name_plural = _("Event Matcher Policies")
