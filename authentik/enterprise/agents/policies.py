"""Global policy check that scopes agents to their allow-listed applications.

An agent may act on *exactly* the applications on its allow-list, and never on an application
its owner cannot access. This is enforced as an authoritative global policy check so every
provider (and the application list) is covered through the single PolicyEngine seam.
"""

from typing import TYPE_CHECKING

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import Application, User, UserTypes
from authentik.policies.models import PolicyBindingModel
from authentik.policies.types import PolicyResult

if TYPE_CHECKING:
    from authentik.enterprise.agents.models import Agent


def _agent_for(user: User) -> Agent | None:
    """Return the Agent MTI child for a user, or None. Memoized on the user instance."""
    if "_agent" not in user.__dict__:
        agent = None
        # Cheap gate: only service accounts can be agents, so ordinary users pay no query.
        if getattr(user, "type", None) == UserTypes.SERVICE_ACCOUNT:
            from authentik.enterprise.agents.models import Agent

            agent = Agent.objects.filter(pk=user.pk).first()
        user.__dict__["_agent"] = agent
    return user.__dict__["_agent"]


def _allowed_app_pks(user: User, agent: Agent) -> set:
    if "_agent_allowed_apps" not in user.__dict__:
        user.__dict__["_agent_allowed_apps"] = set(agent.applications.values_list("pk", flat=True))
    return user.__dict__["_agent_allowed_apps"]


def _owner_can_access(
    user: User, agent: Agent, app: Application, request: HttpRequest | None
) -> bool:
    """Whether the agent's owner passes policy for `app`. Memoized per app on the user.

    Note: called once per application, so an agent listing the whole catalogue does one owner
    PolicyEngine build per app. Acceptable for the low volume of agent-authenticated requests;
    a batched owner evaluation is a possible future optimization.
    """
    cache = user.__dict__.setdefault("_agent_owner_access", {})
    if app.pk not in cache:
        # Imported here to avoid an import cycle (this module is called from PolicyEngine).
        from authentik.policies.engine import PolicyEngine

        engine = PolicyEngine(app, agent.owner, request)
        engine.use_cache = False
        engine.empty_result = AppAccessWithoutBindings.get()
        # The owner is not an agent, so this build does not recurse into this check.
        cache[app.pk] = engine.build().passing
    return cache[app.pk]


def agent_application_access(
    user: User, pbm: PolicyBindingModel, request: HttpRequest | None
) -> PolicyResult | None:
    """Authoritative verdict for an agent accessing an application; None for anything else."""
    if not isinstance(pbm, Application):
        return None
    agent = _agent_for(user)
    if agent is None:
        return None
    if pbm.pk not in _allowed_app_pks(user, agent):
        return PolicyResult(False, _("Agent is not scoped to this application."))
    if not _owner_can_access(user, agent, pbm, request):
        return PolicyResult(False, _("The agent's owner cannot access this application."))
    return PolicyResult(True)
