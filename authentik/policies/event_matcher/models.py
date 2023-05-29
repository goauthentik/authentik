"""Event Matcher models"""
from django.apps import apps
from django.db import models
from django.utils.translation import gettext as _
from rest_framework.serializers import BaseSerializer

from authentik.blueprints.v1.importer import is_model_allowed
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


def model_choices() -> list[tuple[str, str]]:
    """Get a list of all installed models
    Returns a list of tuples containing (dotted.model.path, name)"""
    choices = []
    for model in apps.get_models():
        if model._meta.abstract:
            continue
        if not is_model_allowed(model):
            continue
        name = f"{model._meta.app_label}.{model._meta.model_name}"
        choices.append((name, model._meta.verbose_name))
    return choices


class EventMatcherPolicy(Policy):
    """Passes when Event matches selected criteria."""

    action = models.TextField(
        choices=EventAction.choices,
        blank=True,
        help_text=_(
            "Match created events with this action type. "
            "When left empty, all action types will be matched."
        ),
    )
    app = models.TextField(
        blank=True,
        default="",
        help_text=_(
            "Match events created by selected application. "
            "When left empty, all applications are matched."
        ),
    )
    model = models.TextField(
        blank=True,
        default="",
        help_text=_(
            "Match events created by selected model. "
            "When left empty, all models are matched. When an app is selected, "
            "all the application's models are matched."
        ),
    )
    client_ip = models.TextField(
        blank=True,
        help_text=_(
            "Matches Event's Client IP (strict matching, "
            "for network matching use an Expression Policy)"
        ),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.policies.event_matcher.api import EventMatcherPolicySerializer

        return EventMatcherPolicySerializer

    @property
    def component(self) -> str:
        return "ak-policy-event-matcher-form"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        if "event" not in request.context:
            return PolicyResult(False)
        event: Event = request.context["event"]
        matches = []
        messages = []
        if self.passes_action(request, event):
            matches.append(True)
            messages.append("Action matched.")
        if self.passes_client_ip(request, event):
            matches.append(True)
            messages.append("Client IP matched.")
        if self.passes_app(request, event):
            matches.append(True)
            messages.append("App matched.")
        if self.passes_model(request, event):
            matches.append(True)
            messages.append("Model matched.")
        if len(matches) < 1:
            return PolicyResult(False)
        return PolicyResult(True, *messages)

    def passes_action(self, request: PolicyRequest, event: Event) -> bool:
        """Check if `self.action` matches"""
        if self.action == "":
            return False
        if self.action == event.action:
            return True
        return False

    def passes_client_ip(self, request: PolicyRequest, event: Event) -> bool:
        """Check if `self.client_ip` matches"""
        if self.client_ip == "":
            return False
        if self.client_ip == event.client_ip:
            return True
        return False

    def passes_app(self, request: PolicyRequest, event: Event) -> bool:
        """Check if `self.app` matches"""
        if self.app == "":
            return False
        if self.app == event.app:
            return True
        return False

    def passes_model(self, request: PolicyRequest, event: Event) -> bool:
        """Check if `self.model` is set, and pass if it matches the event's model"""
        if self.model == "":
            return False
        event_model_info = event.context.get("model", {})
        event_model = f"{event_model_info.get('app')}.{event_model_info.get('model_name')}"
        if event_model == self.model:
            return True
        return False

    class Meta(Policy.PolicyMeta):
        verbose_name = _("Event Matcher Policy")
        verbose_name_plural = _("Event Matcher Policies")
