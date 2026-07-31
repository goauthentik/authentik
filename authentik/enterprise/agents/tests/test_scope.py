from django.test import TestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.agents.models import Agent
from authentik.lib.generators import generate_id
from authentik.policies.engine import ListPolicyEngine, PolicyEngine
from authentik.policies.models import PolicyBinding


class AgentScopeTests(TestCase):
    """The agent application allow-list grants + caps access, bounded by the owner."""

    def _app(self) -> Application:
        # No bindings -> open to everyone by default (AppAccessWithoutBindings).
        return Application.objects.create(name=generate_id(), slug=generate_id())

    def _passes(self, app: Application, user) -> bool:
        return PolicyEngine(app, user).build().passing

    def test_unscoped_agent_denied(self):
        """An agent with an empty allow-list reaches nothing, even open apps."""
        owner = create_test_user()
        app = self._app()
        self.assertTrue(self._passes(app, owner))  # owner can access the open app
        agent = Agent.create_for_user(owner)
        self.assertFalse(self._passes(app, agent))

    def test_scoped_agent_allowed(self):
        """An allow-listed app is granted to the agent without any per-agent binding."""
        owner = create_test_user()
        app = self._app()
        agent = Agent.create_for_user(owner)
        agent.applications.add(app)
        self.assertTrue(self._passes(app, agent))

    def test_agent_denied_off_list(self):
        owner = create_test_user()
        app1, app2 = self._app(), self._app()
        agent = Agent.create_for_user(owner)
        agent.applications.add(app1)
        self.assertTrue(self._passes(app1, agent))
        self.assertFalse(self._passes(app2, agent))

    def test_owner_cap(self):
        """An agent can never exceed its owner, even if the app is on its allow-list."""
        owner = create_test_user()
        other = create_test_user()
        app = self._app()
        # Restrict the app to `other` -> the owner cannot access it.
        PolicyBinding.objects.create(target=app, user=other, order=0)
        self.assertFalse(self._passes(app, owner))

        agent = Agent.create_for_user(owner)
        agent.applications.add(app)
        # Scoped, but the owner is denied -> the agent is denied too.
        self.assertFalse(self._passes(app, agent))

        # Grant the owner access -> the agent (re-fetched, fresh per-request memo) is allowed.
        PolicyBinding.objects.create(target=app, user=owner, order=1)
        self.assertTrue(self._passes(app, owner))
        agent = Agent.objects.get(pk=agent.pk)
        self.assertTrue(self._passes(app, agent))

    def test_app_list_filtered_to_scope(self):
        """The application list only returns an agent's in-scope, owner-permitted apps."""
        owner = create_test_user()
        in_scope, off_scope = self._app(), self._app()
        agent = Agent.create_for_user(owner)
        agent.applications.add(in_scope)

        engine = ListPolicyEngine(Application.objects.all(), agent)
        allowed = {app.pk for app in engine.build().result}
        self.assertIn(in_scope.pk, allowed)
        self.assertNotIn(off_scope.pk, allowed)
