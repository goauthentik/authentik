from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.core.models import ActorPolicyInheritance, Application
from authentik.core.tests.utils import create_test_user
from authentik.enterprise.agents.models import Agent
from authentik.lib.generators import generate_id
from authentik.policies.engine import ListPolicyEngine, PolicyEngine
from authentik.policies.models import PolicyBinding


class AgentMirrorTests(TestCase):
    """A MIRROR agent is evaluated as its parent: it passes a policy iff the parent does."""

    def _app(self) -> Application:
        return Application.objects.create(name=generate_id(), slug=generate_id())

    def _passes(self, app: Application, user) -> bool:
        return PolicyEngine(app, user).build().passing

    def _restrict_to(self, app: Application, user) -> None:
        # A user binding makes the app pass only for that user.
        PolicyBinding.objects.create(target=app, user=user, order=0)

    def test_mirror_matches_parent(self):
        parent = create_test_user()
        other = create_test_user()
        allowed, denied = self._app(), self._app()
        self._restrict_to(allowed, parent)
        self._restrict_to(denied, other)

        agent = Agent.create_for_user(parent)
        self.assertEqual(agent.policy_behavior, ActorPolicyInheritance.MIRROR)

        # The agent mirrors its parent exactly.
        self.assertTrue(self._passes(allowed, parent))
        self.assertTrue(self._passes(allowed, agent))
        self.assertFalse(self._passes(denied, parent))
        self.assertFalse(self._passes(denied, agent))

    def test_mirror_tracks_parent_live(self):
        parent = create_test_user()
        other = create_test_user()
        app = self._app()
        self._restrict_to(app, other)  # parent excluded

        agent = Agent.create_for_user(parent)
        self.assertFalse(self._passes(app, agent))

        # Grant the parent access -> the agent gains it live.
        self._restrict_to(app, parent)
        self.assertTrue(self._passes(app, agent))

    def test_none_agent_is_independent(self):
        parent = create_test_user()
        other = create_test_user()
        agent = Agent.create_for_user(parent, policy_behavior=ActorPolicyInheritance.NONE)

        # An open app (no bindings) passes for the independent agent by default...
        self.assertTrue(self._passes(self._app(), agent))
        # ...but a restricted app it has no binding on is denied, regardless of the parent.
        restricted = self._app()
        self._restrict_to(restricted, other)
        self.assertFalse(self._passes(restricted, agent))

    def test_copy_snapshots_parent(self):
        parent = create_test_user()
        app = self._app()
        self._restrict_to(app, parent)  # a binding referencing the parent as a user

        agent = Agent.create_for_user(parent, policy_behavior=ActorPolicyInheritance.COPY)
        # The agent holds its own copy of the parent's binding -> it passes.
        self.assertTrue(self._passes(app, agent))

        # The snapshot is independent: revoking the parent's access does not affect the agent.
        PolicyBinding.objects.filter(user=parent, target=app).delete()
        self.assertFalse(self._passes(app, parent))
        self.assertTrue(self._passes(app, agent))

    def test_policy_behavior_is_immutable(self):
        """policy_behavior may only be chosen at creation."""
        agent = Agent.create_for_user(create_test_user())
        agent = Agent.objects.get(pk=agent.pk)  # fresh load snapshots the original value
        agent.policy_behavior = ActorPolicyInheritance.NONE
        with self.assertRaises(ValidationError):
            agent.save()

    def test_app_list_mirrors_parent(self):
        parent = create_test_user()
        other = create_test_user()
        in_scope, off_scope = self._app(), self._app()
        self._restrict_to(in_scope, parent)
        self._restrict_to(off_scope, other)
        agent = Agent.create_for_user(parent)

        engine = ListPolicyEngine(Application.objects.all(), agent)
        allowed = {app.pk for app in engine.build().result}
        self.assertIn(in_scope.pk, allowed)
        self.assertNotIn(off_scope.pk, allowed)
